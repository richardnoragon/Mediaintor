"""Draft validation and three-way comparisons, independent of Qt/Calibre."""
import math

FIELDS = ('title', 'authors', 'tags', 'series', 'series_index', 'comments', 'cover')


def equal(field, a, b):
    return set(a or []) == set(b or []) if field == 'tags' else a == b


def changes(baseline, draft):
    return {f: draft[f] for f in FIELDS if not equal(f, baseline[f], draft[f])}


def conflicts(baseline, current, pending):
    return [f for f, v in pending.items()
            if not equal(f, baseline[f], current[f]) and not equal(f, v, current[f])]


def validate(record):
    if not record['title'].strip():
        raise ValueError('Title cannot be empty.')
    if not record['authors'] or any(not a.strip() for a in record['authors']):
        raise ValueError('Add at least one non-empty author.')
    if any(not t.strip() or ',' in t for t in record['tags']):
        raise ValueError('Tag names cannot be empty or contain commas because Calibre treats commas as separators.')
    if record['series']:
        try:
            value = float(record['series_index'])
        except (TypeError, ValueError):
            raise ValueError('Series number must be numeric and greater than or equal to zero.') from None
        if not math.isfinite(value) or value < 0:
            raise ValueError('Series number must be finite and greater than or equal to zero.')
    elif record['series_index'] is not None:
        raise ValueError('Series number is inapplicable without a series.')
