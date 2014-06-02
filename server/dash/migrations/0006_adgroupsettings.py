# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations
import __builtin__
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0005_adgroupnetworksettings'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdGroupSettings',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('ad_group', models.ForeignKey(to='dash.AdGroup', to_field=b'id')),
                ('created_datetime', models.DateTimeField(auto_now_add=True)),
                ('status', models.IntegerField(default=2, choices=[(1, b'Active'), (2, b'Inactive')])),
                ('start_date', models.DateField(null=True, blank=True)),
                ('end_date', models.DateField(null=True, blank=True)),
                ('cpc_cc', models.DecimalField(default=0, max_digits=10, decimal_places=4)),
                ('budget_day_cc', models.DecimalField(default=0, max_digits=10, decimal_places=4)),
                ('target_devices', jsonfield.fields.JSONField(default=__builtin__.dict, blank=True)),
                ('target_regions', jsonfield.fields.JSONField(default=__builtin__.dict, blank=True)),
                ('tracking_code', models.TextField(blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
