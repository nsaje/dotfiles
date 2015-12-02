# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0088_scheduledexportreportlog'),
    ]

    operations = [
        migrations.AddField(
            model_name='scheduledexportreportlog',
            name='recipient_emails',
            field=models.CharField(max_length=1024, null=True),
        ),
    ]
