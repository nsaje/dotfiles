# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0010_auto_20140604_1333'),
    ]

    operations = [
        migrations.AddField(
            model_name='adgroupsettings',
            name='created_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, default=1, to_field='id'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='adgroupnetworksettings',
            name='created_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, default=1, to_field='id'),
            preserve_default=False,
        ),
    ]
