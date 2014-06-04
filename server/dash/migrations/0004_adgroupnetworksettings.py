# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0003_adgroup'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdGroupNetworkSettings',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('network', models.CharField(max_length=127, choices=[(b'taboola', b'Taboola'), (b'outbrain', b'Outbrain'), (b'yahoo', b'Yahoo'), (b'nrelate', b'nRelate')])),
                ('ad_group', models.ForeignKey(to='dash.AdGroup', to_field=b'id')),
                ('created_dt', models.DateTimeField(auto_now_add=True)),
                ('state', models.IntegerField(default=2, choices=[(1, b'Active'), (2, b'Inactive')])),
                ('cpc_cc', models.DecimalField(default=0, max_digits=10, decimal_places=4)),
                ('budget_day_cc', models.DecimalField(default=0, max_digits=10, decimal_places=4)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
