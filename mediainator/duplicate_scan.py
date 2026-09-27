"""Read-only duplicate evidence for a frozen catalog; never follows library links."""
from collections import defaultdict
import hashlib
import os
from pathlib import Path
import stat
import time
from .discovery import normalized

class ScanCancelled(Exception):
    pass

def scan_library(root, books, cancelled=lambda:False, progress=lambda message:None, missing_titles=()):
    root=Path(root).resolve(strict=True)
    result=dict(exact=[],similar=[],errors=[],cancelled=False,files_hashed=0,bytes_hashed=0)
    sizes=defaultdict(list);similar=defaultdict(list);last=0
    def check():
        if cancelled():raise ScanCancelled()
    def report(message,force=False):
        nonlocal last
        now=time.monotonic()
        if force or now-last>=.1:progress(message);last=now
    def safe_path(value):
        path=Path(value)
        if not path.is_absolute() or not path.is_relative_to(root):raise ValueError('Path outside the current library')
        for part in (path,*path.parents):
            if part==root:break
            if part.is_symlink():raise ValueError('Symbolic links are excluded')
        if not path.resolve(strict=True).is_relative_to(root):raise ValueError('Path outside the current library')
        return path
    def signature(s):return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
    try:
        report('Preparing library file inventory…',True)
        for book in books:
            check()
            title,author=normalized(book.title),normalized(book.author)
            if title and author not in ('','unknown','unknown author') and not set(getattr(book,'missing_fields',()))&{'title','author'} and book.uuid not in missing_titles:
                similar[(title,author)].append(dict(uuid=book.uuid,title=book.title,author=book.author))
            for fmt,value in book.paths:
                check()
                try:
                    path=safe_path(value);s=path.stat()
                    if not stat.S_ISREG(s.st_mode):raise ValueError('Not a regular file')
                    sizes[(fmt.upper(),s.st_size)].append((book,path,signature(s)))
                except (OSError,ValueError) as exc:result['errors'].append(dict(path=value,error=str(exc)))
        result['similar']=[dict(books=rows) for rows in similar.values() if len({r['uuid'] for r in rows})>1]
        candidates=[(fmt,rows) for (fmt,size),rows in sizes.items() if len({b.uuid for b,_,_ in rows})>1]
        total=sum(len(rows) for _,rows in candidates)
        report(f'Hashing {total} candidate files…',True)
        for fmt,rows in candidates:
            hashes=defaultdict(list)
            for book,path,before in rows:
                check()
                try:
                    safe_path(str(path));fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
                    with os.fdopen(fd,'rb') as stream:
                        if signature(os.fstat(stream.fileno()))!=before:raise ValueError('File changed before hashing')
                        digest=hashlib.sha256()
                        while True:
                            check();chunk=stream.read(1024*1024)
                            if not chunk:break
                            digest.update(chunk);result['bytes_hashed']+=len(chunk)
                            report(f"Hashing {result['files_hashed']} / {total} files · {result['bytes_hashed']//1048576} MiB")
                        if signature(os.fstat(stream.fileno()))!=before or signature(path.stat())!=before:raise ValueError('File changed during hashing')
                    hashes[digest.hexdigest()].append(dict(uuid=book.uuid,title=book.title,author=book.author,path=str(path),signature=before))
                    result['files_hashed']+=1
                except (OSError,ValueError) as exc:result['errors'].append(dict(path=str(path),error=str(exc)))
            for digest,members in hashes.items():
                if len({r['uuid'] for r in members})>1:result['exact'].append(dict(format=fmt,sha256=digest,books=members))
        # Earlier files may have changed while later candidates were read.
        valid=[]
        for group in result['exact']:
            check();stable=True
            for row in group['books']:
                try:
                    if signature(safe_path(row['path']).stat())!=row['signature']:raise ValueError('File changed before scan completion')
                except (OSError,ValueError) as exc:stable=False;result['errors'].append(dict(path=row['path'],error=str(exc)))
            if stable:valid.append(group)
        result['exact']=valid
    except ScanCancelled:
        result['cancelled']=True
        # Cancelled evidence has not passed final coherence verification.
        result['exact']=[]
    report('Cancelled — scan incomplete.' if result['cancelled'] else 'Scan finished.' ,True)
    return result
