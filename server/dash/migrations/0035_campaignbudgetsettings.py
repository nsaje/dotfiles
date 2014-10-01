# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dash', '0034_auto_20140922_1619'),
    ]

    operations = [
        migrations.CreateModel(
            name='CampaignBudgetSettings',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('allocate', models.DecimalField(default=0, verbose_name=b'Allocate amount', max_digits=20, decimal_places=4)),
                ('revoke', models.DecimalField(default=0, verbose_name=b'Revoke amount', max_digits=20, decimal_places=4)),
                ('total', models.DecimalField(default=0, verbose_name=b'Total budget', max_digits=20, decimal_places=4)),
                ('comment', models.CharField(max_length=256)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('campaign', models.ForeignKey(to='dash.Campaign', on_delete=django.db.models.deletion.PROTECT)),
                ('created_by', models.ForeignKey(related_name=b'+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'get_latest_by': 'created_dt',
            },
            bases=(models.Model,),
        ),
    ]
