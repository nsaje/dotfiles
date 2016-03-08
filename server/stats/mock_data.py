from datetime import datetime, timedelta
from random import random

TEST_COLUMNS = 10
TEST_COLUMNS_TYPES = ['int', 'string', 'string', 'string']
TEST_BREAKDOWNS = ['date', 'age', 'ad_group']
TEST_BREAKDOWNS_DATES = [(datetime(2016, 4, 1) + timedelta(days=i)).strftime('%b %d %Y') for i in range(30)]
TEST_BREAKDOWNS_AD_GROUPS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
TEST_BREAKDOWNS_AGES = ['<18', '18-21', '21-30', '30-40', '30-40', '40-50', '50-60', '60-70', '70-80', '80-90', '99+']
TEST_BREAKDOWNS_SEX = ['man', 'woman']


# stats
#   -> data ~ totals
#   -> breakdown (level-1)
#       -> pagination
#       -> rows []
#           -> data ~ totals
#           -> breakdown (level-2)
#               -> pagination
#               -> rows []
#                   -> data ~ totals
#                   -> breakdown (level-2)
#                       -> pagination
#                       -> rows []
#                       -> ...
def generate_random_data(breakdowns, level=0, key='Total'):
    row = {'data': _generate_random_row(key)}

    if level < len(breakdowns):
        breakdown = {}
        row['breakdown'] = breakdown

        keys, pagination = _get_breakdown_keys(breakdowns[level])
        rows = []
        breakdown['rows'] = rows
        breakdown['pagination'] = pagination

        for k in keys:
            r = generate_random_data(breakdowns, level + 1, k)
            rows.append(r)

    return row


def _generate_random_row(key):
    return [key] + [('%.2f' % (random()*10000)) for _ in range(TEST_COLUMNS)]


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

    keys_size = len(keys)
    keys_from = breakdown['range'][0]
    keys_to = min(breakdown['range'][1], keys_size)

    if keys_from >= keys_to or keys_from < 0:
        raise Exception('Out of bounds')

    pagination = {
        'from': keys_from,
        'to': keys_to,
        'count': keys_size
    }
    keys = keys[keys_from:keys_to]

    return keys, pagination
