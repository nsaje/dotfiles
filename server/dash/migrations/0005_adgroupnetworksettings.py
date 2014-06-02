# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0004_adgroup'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdGroupNetworkSettings',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('network', models.ForeignKey(to='dash.Network', to_field=b'id')),
                ('ad_group', models.ForeignKey(to='dash.AdGroup', to_field=b'id')),
                ('created_datetime', models.DateTimeField(auto_now_add=True)),
                ('status', models.IntegerField(default=2, choices=[(1, b'Active'), (2, b'Inactive')])),
                ('cpc_cc', models.DecimalField(default=0, max_digits=10, decimal_places=4)),
                ('budget_day_cc', models.DecimalField(default=0, max_digits=10, decimal_places=4)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
