# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('automation', '0005_proposedadgroupsourcebidcpc'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='proposedadgroupsourcebidcpc',
            name='ad_group',
        ),
        migrations.RemoveField(
            model_name='proposedadgroupsourcebidcpc',
            name='ad_group_source',
        ),
        migrations.RemoveField(
            model_name='proposedadgroupsourcebidcpc',
            name='campaign',
        ),
        migrations.DeleteModel(
            name='ProposedAdGroupSourceBidCpc',
        ),
    ]
