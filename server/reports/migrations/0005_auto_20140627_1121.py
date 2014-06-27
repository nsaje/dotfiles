# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0004_auto_20140626_1615'),
    ]

    operations = [
        migrations.AddField(
            model_name='articlestats',
            name='cost_cc',
            field=models.IntegerField(default=0),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='articlestats',
            name='cpc_cc',
            field=models.IntegerField(default=0),
            preserve_default=True,
        ),
        migrations.RemoveField(
            model_name='articlestats',
            name='cost',
        ),
        migrations.RemoveField(
            model_name='articlestats',
            name='cpc',
        ),
    ]
