"""Visible action names; internal recovery commands remain stable."""
REVIEW_LABELS = {
    'recovery': 'Open recovery draft',
    'import': 'Review pending imports',
    'bulk': 'Review pending batch',
    'metadata': 'Open book editor',
}
DISCARD_LABELS = {
    'recovery': 'Discard preserved draft',
    'import': 'Discard pending imports',
    'bulk': 'Discard pending batch changes',
    'metadata': 'Discard pending save changes',
}

def activity_label(record, action):
    kind = record['source'].get('kind')
    if action == 'review':
        if kind == 'recovery' and not (record['pending'] or record['recovery']):
            return 'Recovery resolved'
        return REVIEW_LABELS.get(kind, 'Review next steps')
    if action == 'discard': return DISCARD_LABELS.get(kind, 'Discard pending work')
    return {'dismiss': 'Hide from action list', 'delete': 'Delete this history record'}[action]
