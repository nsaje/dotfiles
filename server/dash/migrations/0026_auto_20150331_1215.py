# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    def migrate_article_data(apps, schema_editor):
        ContentAd = apps.get_model('dash', 'ContentAd')

        for content_ad in ContentAd.objects.all():
            article = content_ad.article

            content_ad.ad_group = article.ad_group
            content_ad.created_dt = article.created_dt
            content_ad.title = article.title
            content_ad.url = article.url

            content_ad.save()
            article.delete()

    dependencies = [
        ('dash', '0025_auto_20150331_1124'),
    ]

    operations = [
        migrations.RunPython(migrate_article_data)
    ]
