# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dash', '0037_auto_20141001_1141'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccountSettings',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=127)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('archived', models.BooleanField(default=False)),
                ('account', models.ForeignKey(related_name=b'settings', on_delete=django.db.models.deletion.PROTECT, to='dash.Account')),
                ('created_by', models.ForeignKey(related_name=b'+', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-created_dt',),
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='adgroupsettings',
            name='archived',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='campaignsettings',
            name='archived',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
