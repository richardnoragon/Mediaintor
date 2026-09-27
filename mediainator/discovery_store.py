"""Per-library definitions/workflow only; no Calibre metadata writes."""
from copy import deepcopy
import hashlib,json
from pathlib import Path
from .activity import locked
from .import_store import atomic_json
from .discovery import validate_query

class DiscoveryStore:
    def __init__(self,root,library,library_uuid,owner):
        self.identity=dict(path=str(Path(library).resolve()),uuid=library_uuid,owner=owner)
        digest=hashlib.sha256(json.dumps(self.identity,sort_keys=True).encode()).hexdigest()
        self.folder=Path(root)/digest;self.path=self.folder/'state.json'
    def validate(self,data):
        if not isinstance(data,dict) or data.get('schema')!=1 or data.get('identity')!=self.identity:raise ValueError('Discovery state belongs to another library or unsupported version; original retained.')
        if type(data.get('revision')) is not int or data['revision']<0:raise ValueError('Invalid discovery revision.')
        if type(data.get('review_missing_series')) is not bool:raise ValueError('Invalid review preference.')
        for key in ('saved_searches','manual_review'):
            if not isinstance(data.get(key),dict):raise ValueError('Invalid discovery state.')
        if not all(isinstance(k,str) and type(v) is bool for k,v in data['manual_review'].items()):raise ValueError('Invalid review flags.')
        if not isinstance(data.get('acknowledged'),list) or not all(isinstance(v,str) for v in data['acknowledged']):raise ValueError('Invalid warning acknowledgments.')
        names=set()
        for key,item in data['saved_searches'].items():
            if not isinstance(key,str) or not isinstance(item,dict):raise ValueError('Invalid saved search.')
            name=item.get('name')
            if not isinstance(name,str) or not name.strip() or len(name)>120 or name.casefold() in names:raise ValueError('Search names must be nonempty and unique (up to 120 characters).')
            names.add(name.casefold());validate_query(item.get('query'))
        return data
    def load(self):
        try:return self.validate(json.loads(self.path.read_text()))
        except FileNotFoundError:return dict(schema=1,identity=self.identity,revision=0,saved_searches={},manual_review={},acknowledged=[],review_missing_series=False)
    def update(self,expected,change):
        with locked(self.folder):
            current=self.load()
            if current['revision']!=expected:raise ValueError('Discovery state changed. Reload before retrying.')
            updated=deepcopy(current);change(updated);updated['revision']+=1;self.validate(updated)
            atomic_json(self.path,updated)
            if self.load()!=updated:raise ValueError('Discovery update could not be verified.')
            return updated
