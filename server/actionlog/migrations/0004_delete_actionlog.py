# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('actionlog', '0003_auto_20140701_1252'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ActionLog',
        ),
    ]
