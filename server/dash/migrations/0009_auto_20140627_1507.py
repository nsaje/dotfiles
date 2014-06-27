# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0008_article'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='adgroupnetwork',
            unique_together=set([(b'network', b'network_campaign_key')]),
        ),
    ]
