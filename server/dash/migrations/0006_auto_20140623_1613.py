# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0005_adgroupsettings'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdGroupNetwork',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('network', models.ForeignKey(to='dash.Network', to_field=b'id')),
                ('ad_group', models.ForeignKey(to='dash.AdGroup', to_field=b'id')),
                ('network_campaign_key', jsonfield.fields.JSONField(default={}, blank=True)),
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
        migrations.AlterField(
            model_name='adgroupnetworksettings',
            name='network',
            field=models.ForeignKey(to='dash.Network', to_field=b'id', null=True),
        ),
    ]
