# this file is here just so i don't write fixtures by hand
# you can ignore it

import random
import datetime

article_adgroup = [(1, 1), (2, 1), (3, 2), (4, 2), (5, 3), (6, 4), (7, 4), (8, 5), (9, 6)]
dates = [datetime.datetime(2014, 8, 1), datetime.datetime(2014, 8, 2), datetime.datetime(2014, 8, 3)]
ad_group_sources = {
    1: [1, 2],
    2: [1, 2],
    3: [1, 2],
    4: [1, 2],
    5: [2],
    6: [1],
}


def generate_fake_fixtures():
    yaml_entry = '''
- fields:
    datetime: '{datetime}'
    ad_group: {ad_group}
    article: {article}
    source: {source}
    impressions: {impressions}
    clicks: {clicks}
    cost_cc: {cost}
    created_dt: '2014-06-04T09:58:21'
  model: reports.articlestats
  pk: {pk}
    '''
    i = 0
    for article, ad_group in article_adgroup:
        for source in ad_group_sources[ad_group]:
            for dt in dates:
                i += 1
                n_imps = int(random.betavariate(5, 5) * 1000)
                ctr = random.betavariate(5, 300)
                clicks = int(n_imps * ctr)
                cost = int(random.betavariate(5, 5) * 5000)
                print yaml_entry.format(
                    datetime=dt.isoformat(),
                    ad_group=ad_group,
                    article=article,
                    source=source,
                    impressions=n_imps,
                    clicks=clicks,
                    cost=cost,
                    pk=i
                )


if __name__ == '__main__':
    generate_fake_fixtures()
