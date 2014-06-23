# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dash', '0003_adgroup'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdGroupNetworkSettings',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('network', models.ForeignKey(to='dash.Network', to_field=b'id')),
                ('ad_group', models.ForeignKey(to='dash.AdGroup', to_field=b'id')),
                ('created_dt', models.DateTimeField(auto_now_add=True, verbose_name=b'Created at')),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, to_field='id')),
                ('state', models.IntegerField(default=2, choices=[(1, b'Enabled'), (2, b'Paused')])),
                ('cpc_cc', models.DecimalField(null=True, verbose_name=b'CPC', max_digits=10, decimal_places=4, blank=True)),
                ('daily_budget_cc', models.DecimalField(null=True, verbose_name=b'Daily budget', max_digits=10, decimal_places=4, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
