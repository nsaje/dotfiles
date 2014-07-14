# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('actionlog', '0014_auto_20140710_0929'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actionlog',
            name='ad_group_network',
            field=models.ForeignKey(to='dash.AdGroupNetwork', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='actionlog',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='actionlog',
            name='modified_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='actionlog',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='actionlog.ActionLogOrder', null=True),
        ),
    ]
