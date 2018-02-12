# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0039_campaignsettings_system_user'),
    ]

    operations = [
        migrations.RenameField(
            model_name='campaignsettings',
            old_name='automatic_landing_mode',
            new_name='automatic_campaign_stop',
        ),
    ]
