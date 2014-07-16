# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

import reports.models
import dash.models


def migrate_data(apps, schema_editor):
    article_statss = reports.models.ArticleStats.objects.all()
    for article_stats in article_statss:
        article_stats.source = dash.models.Source.objects.get(id=article_stats.network.id)
        article_stats.save()


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0009_auto_20140716_1507'),
        ('dash', '0021_auto_20140716_1508')
    ]

    operations = [
        migrations.RunPython(migrate_data)
    ]
