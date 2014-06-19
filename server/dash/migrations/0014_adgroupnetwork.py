# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0013_auto_20140610_1257'),
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
    ]
