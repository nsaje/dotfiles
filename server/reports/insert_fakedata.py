import models

import fakedata

articles = []

### Run like this: ./manage.py shell < reports/insert_fakedata.py

# Make sure you have ad groups with ids from 1 to 7 in db.

for i, d in enumerate(fakedata.DATA):
    if d['ad_group'] in (4, 5, 6):
        if d['article'] not in articles:
            article = models.Article(
                pk=d['article'],
                url='http://test{}.com'.format(i),
                title='Test Article {0}'.format(i),
                ad_group_id=d['ad_group']
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
            cpc=d['cpc'],
            cost=d['cost']
        )
        article_stats.save()
