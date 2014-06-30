import datetime
import models
from dash import models as dm

import fakedata

articles = []

### Run like this:
### ./manage.py shell
### import reports.insert_fakedata

# Make sure you have ad groups with ids from 1 to 7 in db.

for i, d in enumerate(fakedata.DATA):
    if d['ad_group'] in (4,5,6,):
        if d['article'] not in articles:
            article = dm.Article(
                pk=d['article'],
                url='http://test{}.com'.format(i),
                title='Test Article {0}'.format(i),
                ad_group_id=d['ad_group'],
                created_dt=datetime.datetime.utcnow()
            )
            article.save()
            articles.append(article.pk)

        article_stats = models.ArticleStats(
            datetime=d['date'],
            ad_group_id=d['ad_group'],
            article_id=d['article'],
            network_id=d['network'],
            impressions=d['impressions'],
            clicks=d['clicks'],
            cost_cc=int(d['cost'] * 10000),
        )
        article_stats.save()
