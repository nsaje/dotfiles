# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0009_auto_20140627_1507'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adgroupnetworksettings',
            name='created_by',
            field=models.ForeignKey(to_field='id', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
