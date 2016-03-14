# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zemauth', '0016_auto_20160308_1703'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_test_user',
            field=models.BooleanField(default=False, help_text=b'Designates whether user is an internal testing user and will not contribute towards certain statistics.'),
        ),
    ]
