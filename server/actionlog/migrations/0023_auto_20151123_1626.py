# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('actionlog', '0022_auto_20151103_0957'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actionlog',
            name='action',
            field=models.CharField(db_index=True, max_length=100, choices=[(b'get_reports_by_publisher', b'Get reports by publisher'), (b'insert_content_ad', b'Insert content ad'), (b'set_publisher_blacklist', b'Set publisher blacklist'), (b'get_content_ad_status', b'Get content ad status'), (b'create_campaign', b'Create campaign'), (b'get_reports', b'Get reports'), (b'set_campaign_state', b'Set campaign state'), (b'insert_content_ad_batch', b'Insert content ad batch'), (b'update_content_ad', b'Update content ad'), (b'submit_ad_group', b'Submit ad group to approval'), (b'set_property', b'Set property'), (b'get_campaign_status', b'Get campaign status')]),
        ),
    ]
