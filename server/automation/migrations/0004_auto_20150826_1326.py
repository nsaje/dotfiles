# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0064_remove_sourcetype_available_actions_new'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('automation', '0003_auto_20150819_1134'),
    ]

    operations = [
        migrations.CreateModel(
            name='CampaignBudgetDepletionNotification',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, null=True, verbose_name=b'Created at', db_index=True)),
                ('available_budget', models.DecimalField(decimal_places=4, default=0, max_digits=20, blank=True, null=True, verbose_name=b'Budget available at creation')),
                ('yesterdays_spend', models.DecimalField(decimal_places=4, default=0, max_digits=20, blank=True, null=True, verbose_name=b"Campaign's yesterday's spend")),
                ('account_manager', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, null=True)),
                ('campaign', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to='dash.Campaign')),
            ],
        ),
        migrations.RemoveField(
            model_name='campaignbudgetdepletionnotifaction',
            name='account_manager',
        ),
        migrations.RemoveField(
            model_name='campaignbudgetdepletionnotifaction',
            name='campaign',
        ),
        migrations.DeleteModel(
            name='CampaignBudgetDepletionNotifaction',
        ),
    ]
