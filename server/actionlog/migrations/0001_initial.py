# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields
from django.conf import settings


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
                ('action', models.IntegerField(choices=[(b'get_reports', b'Get reports'), (b'set_property', b'Set property'), (b'stop_campaign', b'Stop campaign'), (b'get_campaign_status', b'Get campaign status')])),
                ('status', models.IntegerField(default=1, choices=[(-1, b'Failed'), (2, b'Executed'), (3, b'Aborted'), (1, b'Waiting')])),
                ('type', models.IntegerField(choices=[(1, b'Automatic'), (2, b'Manual')])),
                ('ad_group', models.ForeignKey(to='dash.AdGroup', to_field=b'id')),
                ('network', models.ForeignKey(to='dash.Network', to_field=b'id')),
                ('payload', jsonfield.fields.JSONField(default=[], blank=True)),
                ('created_datetime', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at', null=True)),
                ('modified_datetime', models.DateTimeField(auto_now=True, verbose_name=b'Modified at', null=True)),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, to_field='id')),
                ('modified_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, to_field='id')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
