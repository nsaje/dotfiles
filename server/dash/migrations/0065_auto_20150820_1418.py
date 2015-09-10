# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dash', '0064_remove_sourcetype_available_actions_new'),
    ]

    operations = [
        migrations.AddField(
            model_name='accountsettings',
            name='default_account_manager',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='accountsettings',
            name='default_sales_representative',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
