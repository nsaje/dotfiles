# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0033_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='modified_by',
            field=models.ForeignKey(related_name=b'+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='adgroup',
            name='modified_by',
            field=models.ForeignKey(related_name=b'+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='adgroupsettings',
            name='ad_group',
            field=models.ForeignKey(related_name=b'settings', on_delete=django.db.models.deletion.PROTECT, to='dash.AdGroup'),
        ),
        migrations.AlterField(
            model_name='adgroupsettings',
            name='created_by',
            field=models.ForeignKey(related_name=b'+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='adgroupsourcesettings',
            name='ad_group_source',
            field=models.ForeignKey(related_name=b'settings', on_delete=django.db.models.deletion.PROTECT, to='dash.AdGroupSource', null=True),
        ),
        migrations.AlterField(
            model_name='adgroupsourcesettings',
            name='created_by',
            field=models.ForeignKey(related_name=b'+', on_delete=django.db.models.deletion.PROTECT, blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='modified_by',
            field=models.ForeignKey(related_name=b'+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='campaignsettings',
            name='account_manager',
            field=models.ForeignKey(related_name=b'+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='campaignsettings',
            name='campaign',
            field=models.ForeignKey(related_name=b'settings', on_delete=django.db.models.deletion.PROTECT, to='dash.Campaign'),
        ),
        migrations.AlterField(
            model_name='campaignsettings',
            name='created_by',
            field=models.ForeignKey(related_name=b'+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='campaignsettings',
            name='sales_representative',
            field=models.ForeignKey(related_name=b'+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
