# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields
import django.db.models.deletion
from django.conf import settings
import actionlog.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('actionlog', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActionLog',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('action', models.CharField(max_length=100, choices=[(b'get_reports', b'Get reports'), (b'set_campaign_state', b'Stop campaign'), (b'set_property', b'Set property'), (b'get_campaign_status', b'Get campaign status')])),
                ('state', models.IntegerField(default=1, choices=[(-1, b'Failed'), (2, b'Success'), (3, b'Aborted'), (1, b'Waiting')])),
                ('action_type', models.IntegerField(choices=[(1, b'Automatic'), (2, b'Manual')])),
                ('message', models.TextField(blank=True)),
                ('payload', jsonfield.fields.JSONField(default={}, blank=True)),
                ('expiration_dt', models.DateTimeField(default=actionlog.models._due_date_default, null=True, blank=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at', null=True)),
                ('modified_dt', models.DateTimeField(auto_now=True, verbose_name=b'Modified at', null=True)),
                ('ad_group_source', models.ForeignKey(to='dash.AdGroupSource', on_delete=django.db.models.deletion.PROTECT)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('modified_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': (b'-created_dt',),
                'permissions': ((b'manual_view', b'Can view manual ActionLog actions'), (b'manual_acknowledge', b'Can acknowledge manual ActionLog actions')),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ActionLogOrder',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('order_type', models.IntegerField(choices=[(3, b'AdGroup Settings Update'), (2, b'Stop all'), (1, b'Fetch all'), (5, b'Fetch status'), (4, b'Fetch reports')])),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='actionlog',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='actionlog.ActionLogOrder', null=True),
            preserve_default=True,
        ),
    ]
