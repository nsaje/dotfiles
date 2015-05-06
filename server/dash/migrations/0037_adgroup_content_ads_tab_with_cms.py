# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0036_uploadbatch_num_errors'),
    ]

    operations = [
        migrations.AddField(
            model_name='adgroup',
            name='content_ads_tab_with_cms',
            field=models.BooleanField(default=False, verbose_name=b'Content ads tab with CMS'),
            preserve_default=True,
        ),
    ]
