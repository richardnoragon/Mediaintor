"""Local, book-specific feedback and mutually exclusive batch outcome counts."""
LABELS={'title':'Title','authors':'Authors','tags':'Tags','cover':'Cover','series':'Series','series_index':'Series number','comments':'Description'}
def save_feedback(title,saved=(),remaining=(),errors=None):
    fields=lambda values:', '.join(LABELS.get(v,v) for v in sorted(values))
    errors=errors or {}
    if remaining or errors:
        message=f'Save incomplete for {title}. Saved: {fields(saved) or "none"}. Remaining: {fields(set(remaining)|set(errors)) or "verification required"}.'
        if errors:message+=' '+ '; '.join(f'{LABELS.get(k,k)}: {v}' for k,v in errors.items())
        return message
    if not saved:return f'No changes to save for {title}.'
    return f'Saved metadata for {title}. Fields changed: {fields(saved)}.'

def batch_counts(batch):
    counts=dict(completed=0,failed=0,pending=0,excluded=0,discarded=0,conflicts=0,unverified=0,partial=0,unchanged=0)
    for item in batch['items']:
        state=item['state'];bucket=state if state in ('failed','excluded','discarded') else 'completed' if state=='complete' else 'pending'
        counts[bucket]+=1
        if state=='conflict':counts['conflicts']+=1
        if state in ('inflight','unverified'):counts['unverified']+=1
        if state!='complete' and item.get('applied'):counts['partial']+=1
        if state=='complete' and not item.get('applied'):counts['unchanged']+=1
    return counts

def may_have_writes(batch):
    return any(i.get('applied') or 'attempt_before' in i or i['state'] in ('inflight','unverified') for i in batch['items'])

def batch_feedback(batch,phase='preview'):
    c=batch_counts(batch);name='Revert' if batch.get('kind')=='revert' else 'Bulk edit'
    if phase=='cancel' and not may_have_writes(batch):return 'Cancelled — no books changed.'
    if phase=='preview' and c['pending']+c['failed']:
        header=f'{name} preview ready. {c["pending"]+c["failed"]} books require review. Confirmation required before writes.'
    elif phase=='cancel':header=f'{name} preview closed. Existing changes and pending work retained.'
    elif phase=='interrupted' and c['pending']+c['failed']:header=f'{name} interrupted.'
    elif phase=='failed' or c['failed']:header=f'{name} failed or incomplete.'
    elif c['pending']:header=f'{name} incomplete; review pending work.'
    else:header=f'{name} completed.'
    return (header+f'\n{c["completed"]} completed · {c["failed"]} failed · {c["pending"]} pending.'
            +f'\n{c["excluded"]} excluded · {c["discarded"]} discarded · {c["unchanged"]} completed without changes.'
            +f'\nPending includes {c["conflicts"]} conflicts and {c["unverified"]} requiring verification; {c["partial"]} unfinished books have saved fields.')
