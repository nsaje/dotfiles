# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0006_auto_20140623_1613'),
    ]

    operations = [
        migrations.AddField(
            model_name='network',
            name='type',
            field=models.CharField(max_length=127, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.RemoveField(
            model_name='network',
            name='slug',
        ),
    ]
