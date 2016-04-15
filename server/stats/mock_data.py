from datetime import datetime, timedelta
import random

TEST_COLUMNS = 20
TEST_COLUMNS_TYPES = ['int', 'string', 'string', 'string']
TEST_BREAKDOWNS = ['date', 'age', 'ad_group']
TEST_BREAKDOWNS_DATES = [(datetime(2016, 4, 1) + timedelta(days=i)).strftime('%b %d %Y') for i in range(30)]
TEST_BREAKDOWNS_AD_GROUPS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
TEST_BREAKDOWNS_AGES = ['<18', '18-21', '21-30', '30-40', '40-50', '50-60', '60-70', '70-80', '80-90', '99+']
TEST_BREAKDOWNS_SEX = ['man', 'woman']


# <breakdown>
#   -> level
#   -> position - [a,b,c]
#   -> pagination - from, to, size, count
#   -> rows []
#       -> row
#           -> data
#           -> <breakdown> - (level + 1)
#
# level 0 -> wrapper for total row and it's breakdown
# level 1 -> first level breakdown - original rows  with potential breakdown
# level 2-n -> breakdowns
def generate_random_breakdowns(breakdowns, level):
    top_level_row = _generate_random_breakdown(breakdowns, level=1, position=(0,))
    top_level_breakdown = {
        'rows': [top_level_row],
        'level': 0
    }
    return _get_breakdowns_for_level(top_level_breakdown, level)


def _get_breakdowns_for_level(breakdown, level):
    breakdowns = [breakdown]
    for _ in range(0, level):
        nested_breakdowns = []
        for b in breakdowns:
            for row in b['rows']:
                nested_breakdowns += [row['breakdown']]
        breakdowns = nested_breakdowns
    return breakdowns


def _generate_random_breakdown(breakdowns, level=1, position=(0,), key='Total'):
    row = {
        'stats': _generate_random_stats(key),
    }

    if level <= len(breakdowns):
        breakdown = {}
        row['breakdown'] = breakdown

        keys, pagination = _get_breakdown_keys(breakdowns[level - 1])
        rows = []
        breakdown['rows'] = rows
        breakdown['pagination'] = pagination
        breakdown['level'] = level
        breakdown['position'] = position

        for idx, k in enumerate(keys):
            child_position = position + (pagination['from'] + idx, )
            r = _generate_random_breakdown(breakdowns, level + 1, child_position, k)
            rows.append(r)

    return row


def _generate_random_stats(key):
    if key == 'Total':
        return [key] + [('%.2f' % (random.uniform(10000, 1000000))) for _ in range(TEST_COLUMNS-1)]
    return [key] + [('%.2f' % (random.uniform(100, 1000))) for _ in range(TEST_COLUMNS-1)]


def _get_breakdown_keys(breakdown):
    keys = None
    if breakdown['name'] == 'date':
        keys = TEST_BREAKDOWNS_DATES
    elif breakdown['name'] == 'age':
        keys = TEST_BREAKDOWNS_AGES
    elif breakdown['name'] == 'ad_group':
        keys = TEST_BREAKDOWNS_AD_GROUPS
    elif breakdown['name'] == 'sex':
        keys = TEST_BREAKDOWNS_SEX

    keys_count = len(keys)
    keys_from = breakdown['range'][0]
    keys_to = breakdown['range'][1]
    keys_to = min(keys_to, keys_count) if keys_to > 0 else keys_count

    if keys_from >= keys_to or keys_from < 0:
        raise Exception('Out of bounds')

    pagination = {
        'from': keys_from,
        'to': keys_to,
        'size': keys_to - keys_from,
        'count': keys_count
    }
    keys = keys[keys_from:keys_to]

    return keys, pagination
