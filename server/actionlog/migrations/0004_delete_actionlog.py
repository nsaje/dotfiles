# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('actionlog', '0003_auto_20140701_1252'),
        ('dash', '0009_auto_20140627_1507'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ActionLog',
        ),
        migrations.CreateModel(
            name='ActionLog',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('action', models.CharField(max_length=100, choices=[(b'get_reports', b'Get reports'), (b'set_campaign_state', b'Stop campaign'), (b'set_property', b'Set property'), (b'get_campaign_status', b'Get campaign status')])),
                ('action_status', models.IntegerField(default=1, choices=[(-1, b'Failed'), (2, b'Success'), (3, b'Aborted'), (1, b'Waiting')])),
                ('action_type', models.IntegerField(choices=[(1, b'Automatic'), (2, b'Manual')])),
                ('ad_group_network', models.ForeignKey(to='dash.AdGroupNetwork', to_field='id')),
                ('payload', jsonfield.fields.JSONField(default=[], blank=True)),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at', null=True)),
                ('modified_dt', models.DateTimeField(auto_now=True, verbose_name=b'Modified at', null=True)),
                ('created_by', models.ForeignKey(to_field='id', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('modified_by', models.ForeignKey(to_field='id', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
