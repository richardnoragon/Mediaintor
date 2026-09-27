"""One acknowledgment path for the workbench and saved-record editor."""
from .discovery import DiscoveryIndex

class ReviewService:
    def __init__(self,host):self.host=host
    def review_records(self):return self.host.import_store().review_records()
    def review_needed(self):
        _,state,warnings=self.host.discovery_context()
        return {uid for uid,reasons in DiscoveryIndex(self.host.books,state,warnings).reasons.items() if reasons}
    def mark_reviewed(self,uuid):
        store,state,warnings=self.host.discovery_context();index=DiscoveryIndex(self.host.books,state,warnings)
        acknowledge(store,state,index,{uuid})
        self.host.review_cache=None
        if self.host.discovery_dialog:self.host.discovery_dialog.reload()
    def reasons(self,book):
        _,state,warnings=self.host.discovery_context()
        return DiscoveryIndex((book,),state,warnings).reasons.get(book.uuid,[])

def acknowledge(store,state,index,selected,reviewed=True):
    def change(data):
        for uid in selected:
            if reviewed:data['manual_review'].pop(uid,None)
            else:data['manual_review'][uid]=True
        if reviewed:data['acknowledged']=sorted(set(data['acknowledged']).union(*(index.warning_ids.get(uid,[]) for uid in selected)))
    return store.update(state['revision'],change)
