# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0003_adgroupnetworksettings_adgroupsettings'),
    ]

    operations = [
        migrations.AddField(
            model_name='adgroup',
            name='networks',
            field=models.ManyToManyField(to='dash.Network', through='dash.AdGroupNetwork'),
            preserve_default=True,
        ),
    ]
