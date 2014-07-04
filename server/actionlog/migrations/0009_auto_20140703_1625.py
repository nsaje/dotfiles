# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('actionlog', '0008_auto_20140703_1456'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='actionlog',
            options={'ordering': (b'-created_dt',)},
        ),
        migrations.AlterField(
            model_name='actionlog',
            name='order',
            field=models.ForeignKey(blank=True, to='actionlog.ActionLogOrder', null=True),
        ),
    ]
