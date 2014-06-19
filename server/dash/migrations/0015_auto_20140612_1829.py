# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0014_adgroupnetwork'),
    ]

    operations = [
        migrations.CreateModel(
            name='ZweiSettingsOrder',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('ad_group_network', models.ForeignKey(to='dash.AdGroupNetwork', to_field='id')),
                ('ad_group_settings', models.ForeignKey(to_field=b'id', blank=True, to='dash.AdGroupSettings', null=True)),
                ('ad_group_network_settings', models.ForeignKey(to_field=b'id', blank=True, to='dash.AdGroupNetworkSettings', null=True)),
                ('progress', models.IntegerField(default=2, choices=[(1, b'Ok'), (3, b'Working'), (-1, b'Error'), (2, b'Waiting')])),
                ('created_dt', models.DateTimeField(auto_now_add=True, null=True)),
                ('completed_dt', models.DateTimeField(null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='adgroupnetworksettings',
            name='ad_group_network',
            field=models.ForeignKey(to='dash.AdGroupNetwork', to_field='id', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='adgroup',
            name='networks',
            field=models.ManyToManyField(to='dash.Network', through='dash.AdGroupNetwork'),
            preserve_default=True,
        ),
        migrations.RemoveField(
            model_name='adgroupnetworksettings',
            name='network',
        ),
    ]
