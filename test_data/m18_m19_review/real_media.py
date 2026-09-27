import json,subprocess,hashlib
from pathlib import Path
from uuid import uuid4
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPdfWriter,QPainter
from mediainator.paper_store import PaperStore
from mediainator.paper_import import plan as paper_plan
from mediainator.music_scan import plan as music_plan
app=QApplication.instance() or QApplication([])
base=Path('test_data/m18_m19_review/real_media');base.mkdir(parents=True,exist_ok=True)
pdf=base/'Research.pdf';writer=QPdfWriter(str(pdf));writer.setTitle('Preservation research fixture');writer.setCreator('Media-inator review')
painter=QPainter(writer);painter.drawText(200,500,'UniqueResearchToken DOI 10.5555/review.2026');painter.end();del writer
profile=str(uuid4());store=PaperStore(base/profile,profile);store.initialize()
before=(pdf.read_bytes(),pdf.stat().st_mtime_ns)
result=paper_plan([pdf],store.load(),{},set())
proposal=result.proposals[0]
assert 'UniqueResearchToken' in proposal.text,proposal
store.import_document(pdf,'managed',item_fields=proposal.fields,text=proposal.text,expected=(proposal.size,proposal.sha256))
assert before==(pdf.read_bytes(),pdf.stat().st_mtime_ns)
assert store.search_documents('UniqueResearchToken')
audio=base/'audio'
for fmt in ['flac','mp3']:
 folder=audio/fmt/'Review Album';folder.mkdir(parents=True,exist_ok=True)
 for n in [1,2]:
  target=folder/f'{n:02d} - Track {n}.{fmt}'
  subprocess.run(['ffmpeg','-nostdin','-v','error','-y','-f','lavfi','-i','sine=frequency=440:duration=0.15','-metadata','album=Review Album','-metadata','album_artist=Review Artist','-metadata',f'title=Track {n}','-metadata',f'track={n}',str(target)],check=True)
music=music_plan([audio],[],set())
assert len(music.groups) == 1
assert len(music.groups[0].editions()) == 1
assert len(music.groups[0].editions()[0]['copies']) == 2
assert [t['number'] for t in music.groups[0].editions()[0]['tracks']] == [1,2]
summary={'pdf_tools':result.tools,'pdf_text_search':True,'pdf_original_unchanged':True,'music_plan':repr(music)}
(base/'report.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
