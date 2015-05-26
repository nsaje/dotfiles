# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0045_auto_20150511_1259'),
    ]

    operations = [
        migrations.AlterField(
            model_name='demoadgrouprealadgroup',
            name='demo_ad_group',
            field=models.OneToOneField(related_name='+', on_delete=django.db.models.deletion.PROTECT, to='dash.AdGroup'),
        ),
        migrations.AlterField(
            model_name='demoadgrouprealadgroup',
            name='real_ad_group',
            field=models.OneToOneField(related_name='+', on_delete=django.db.models.deletion.PROTECT, to='dash.AdGroup'),
        ),
        migrations.AlterField(
            model_name='source',
            name='content_ad_submission_type',
            field=models.IntegerField(default=1, choices=[(1, b'Default'), (3, b'Submit whole batch at once'), (2, b'One submission per ad group')]),
        ),
        migrations.AlterField(
            model_name='sourceaction',
            name='action',
            field=models.IntegerField(serialize=False, primary_key=True, choices=[(10, b'Can modify adgroup name'), (7, b'Can modify end date'), (5, b'Has 3rd party dashboard'), (11, b'Can modify ad group IAB category'), (4, b'Can manage content ads'), (3, b'Can update daily budget'), (6, b'Can modify start date'), (9, b'Can modify tracking codes'), (1, b'Can update state'), (2, b'Can update CPC'), (8, b'Can modify device and geo targeting'), (12, b'Update tracking codes on content ads')]),
        ),
    ]
