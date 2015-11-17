# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zemauth', '0041_auto_20150904_0844'),
    ]

    operations = [
        migrations.RunSQL(
            "UPDATE auth_permission SET name='Can view campaign''s settings tab.' WHERE codename='campaign_settings_view';",
            "UPDATE auth_permission SET name='Can view campaign''s agency tab.' WHERE codename='campaign_settings_view';",
        ),
    ]
