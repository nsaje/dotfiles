# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from dash import constants


def set_contentad_state(apps, schema_editor):
    ContentAd = apps.get_model('dash', 'ContentAd')
    ContentAdSource = apps.get_model('dash', 'ContentAdSource')

    for content_ad in ContentAd.objects.all():
        content_ad_sources = ContentAdSource.objects.filter(content_ad=content_ad)
        if any(s.state == constants.ContentAdSourceState.ACTIVE for s in content_ad_sources):
            content_ad.state = constants.ContentAdSourceState.ACTIVE
        else:
            content_ad.state = constants.ContentAdSourceState.INACTIVE
        content_ad.save()


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0037_contentad_state'),
    ]

    operations = [
        migrations.RunPython(set_contentad_state)
    ]
