# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('actionlog', '0017_auto_20150331_1124'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actionlog',
            name='action',
            field=models.CharField(db_index=True, max_length=100, choices=[(b'insert_content_ad', b'Insert content ad'), (b'get_content_ad_status', b'Get content ad status'), (b'create_campaign', b'Create campaign'), (b'get_reports', b'Get reports'), (b'set_campaign_state', b'Set campaign state'), (b'update_content_ad', b'Update content ad'), (b'submit_ad_group', b'Submit ad group to approval'), (b'set_property', b'Set property'), (b'get_campaign_status', b'Get campaign status')]),
        ),
    ]
