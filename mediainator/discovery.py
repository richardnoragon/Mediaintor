"""Pure discovery rules: factual completeness is independent of review workflow."""
import unicodedata

def normalized(value):return ' '.join(unicodedata.normalize('NFKC',value).casefold().split())

FIELDS={'reading_status','missing_metadata','series','tag'}
MISSING={'title','author','cover','series'}
def validate_query(query):
    if not isinstance(query,dict) or query.get('version')!=1 or query.get('mode') not in ('all','any'):raise ValueError('Unsupported search definition.')
    if not isinstance(query.get('text'),str) or len(query['text'])>2000:raise ValueError('Invalid search text.')
    rows=query.get('conditions')
    if not isinstance(rows,list) or len(rows)>100:raise ValueError('Invalid search conditions.')
    for row in rows:
        if not isinstance(row,dict) or row.get('field') not in FIELDS or not isinstance(row.get('value'),str) or not row['value'].strip() or len(row['value'])>500:raise ValueError('Invalid search condition.')
        if row['field']=='missing_metadata' and row['value'] not in MISSING:raise ValueError('Unknown missing metadata field.')
    if not isinstance(query.get('formats',[]),list) or not all(isinstance(v,str) for v in query.get('formats',[])):raise ValueError('Invalid format narrowing.')
    if query.get('sort','title_asc') not in ('title_asc','title_desc','author_asc'):raise ValueError('Invalid search sort.')
    if type(query.get('review_only',False)) is not bool:raise ValueError('Invalid review queue setting.')
    outer=query.get('catalog_filters',{})
    if not isinstance(outer,dict) or set(outer)-{'tags','statuses'} or not all(isinstance(v,list) and all(isinstance(x,str) for x in v) for v in outer.values()):raise ValueError('Invalid catalog narrowing.')
    return query

def empty_query():return dict(version=1,text='',mode='all',conditions=[])

def warning_id(record,reason):return ':'.join((record.get('source_batch',''),record.get('operation_uuid',''),reason))

class DiscoveryIndex:
    def __init__(self,books,state=None,warnings=()):
        self.books=tuple(books);self.state=state or {};self.rows={};self.facets={f:{} for f in FIELDS};self.reasons={};self.warning_ids={}
        bybook={};acknowledged=set(self.state.get('acknowledged',[]))
        for record in warnings:bybook.setdefault(record['destination_uuid'],[]).append(record)
        for n,book in enumerate(self.books):
            facts=set(getattr(book,'missing_fields',()))
            if not book.title.strip():facts.add('title')
            if normalized(book.author) in ('','unknown','unknown author'):facts.add('author')
            if not book.cover:facts.add('cover')
            if not book.series.strip():facts.add('series')
            warning_reasons=[];ids=[]
            for record in bybook.get(book.uuid,[]):
                for reason in record.get('missing',[]):
                    if reason=='title' and book.title==record.get('title'):facts.add('title')
                    identity=warning_id(record,reason);ids.append(identity)
                    if not record.get('reviewed') and identity not in acknowledged:warning_reasons.append('Import warning: '+reason)
            self.warning_ids[book.uuid]=ids
            reasons=['Missing '+f for f in sorted(facts) if f!='series' or self.state.get('review_missing_series',False)]
            if self.state.get('manual_review',{}).get(book.uuid):reasons.append('Manually flagged')
            self.reasons[book.uuid]=reasons+warning_reasons
            self.rows[n]=tuple(normalized(v) for v in (book.title,book.author,book.series))
            for field,values in [('tag',book.tags),('series',(book.series,)),('reading_status',(book.reading_status,)),('missing_metadata',facts)]:
                for value in values:
                    if value:self.facets[field].setdefault(normalized(value),set()).add(n)
        self.ordered=sorted(range(len(self.books)),key=lambda i:(normalized(self.books[i].title),self.books[i].id))
    def query(self,query,review_only=False):
        validate_query(query);sets=[self.facets[row['field']].get(normalized(row['value']),set()) for row in query['conditions']]
        matched=(set.intersection(*sets) if query['mode']=='all' else set.union(*sets)) if sets else set(range(len(self.books)))
        text=normalized(query['text'])
        outer=query.get('catalog_filters',{});tags=set(outer.get('tags',[]));statuses=set(outer.get('statuses',[]))
        formats=set(query.get('formats',[]));review_only=review_only or query.get('review_only',False)
        result=[self.books[i] for i in self.ordered if i in matched and (not text or any(text in v for v in self.rows[i])) and (not tags or tags.intersection(self.books[i].tags)) and (not statuses or self.books[i].reading_status in statuses) and (not formats or formats.intersection(self.books[i].formats)) and (not review_only or self.reasons.get(self.books[i].uuid))]
        if query.get('sort')=='title_desc':result.reverse()
        elif query.get('sort')=='author_asc':result.sort(key=lambda b:(normalized(b.author),normalized(b.title),b.id))
        return result
