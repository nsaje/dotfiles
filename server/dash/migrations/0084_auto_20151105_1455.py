# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0083_scheduledreport_scheduledreportrecipient'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='scheduledreportrecipient',
            unique_together=set([('report', 'email')]),
        ),
    ]
