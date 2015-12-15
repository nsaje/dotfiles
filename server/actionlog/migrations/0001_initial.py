# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields
import django.db.models.deletion
from django.conf import settings
import actionlog.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dash', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActionLog',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('action', models.CharField(db_index=True, max_length=100, choices=[(b'get_reports_by_publisher', b'Get reports by publisher'), (b'insert_content_ad', b'Insert content ad'), (b'set_publisher_blacklist', b'Set publisher blacklist'), (b'get_content_ad_status', b'Get content ad status'), (b'create_campaign', b'Create campaign'), (b'get_reports', b'Get reports'), (b'set_campaign_state', b'Set campaign state'), (b'insert_content_ad_batch', b'Insert content ad batch'), (b'update_content_ad', b'Update content ad'), (b'submit_ad_group', b'Submit ad group to approval'), (b'set_property', b'Set property'), (b'get_campaign_status', b'Get campaign status')])),
                ('state', models.IntegerField(default=1, db_index=True, choices=[(-1, b'Failed'), (1, b'Waiting'), (2, b'Success'), (3, b'Aborted'), (4, b'Delayed')])),
                ('action_type', models.IntegerField(db_index=True, choices=[(1, b'Automatic'), (2, b'Manual')])),
                ('message', models.TextField(blank=True)),
                ('payload', jsonfield.fields.JSONField(default={}, blank=True)),
                ('expiration_dt', models.DateTimeField(default=actionlog.models._due_date_default, null=True, blank=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, null=True, verbose_name=b'Created at', db_index=True)),
                ('modified_dt', models.DateTimeField(auto_now=True, null=True, verbose_name=b'Modified at', db_index=True)),
                ('ad_group_source', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='dash.AdGroupSource', null=True)),
                ('content_ad_source', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='dash.ContentAdSource', null=True)),
                ('created_by', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('modified_by', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('-created_dt',),
                'permissions': (('manual_view', 'Can view manual ActionLog actions'), ('manual_acknowledge', 'Can acknowledge manual ActionLog actions')),
            },
        ),
        migrations.CreateModel(
            name='ActionLogOrder',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('order_type', models.IntegerField(choices=[(3, b'AdGroup Settings Update'), (1, b'Fetch all'), (7, b'Get content ad status'), (6, b'Create campaign'), (2, b'Stop all'), (4, b'Fetch reports'), (5, b'Fetch status')])),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at', null=True)),
            ],
        ),
        migrations.AddField(
            model_name='actionlog',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='actionlog.ActionLogOrder', null=True),
        ),
        migrations.AlterIndexTogether(
            name='actionlog',
            index_together=set([('id', 'created_dt')]),
        ),
    ]
