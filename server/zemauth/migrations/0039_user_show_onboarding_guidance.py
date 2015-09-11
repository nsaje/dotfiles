# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zemauth', '0013_auto_20150708_1150'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='show_onboarding_guidance',
            field=models.BooleanField(default=False, help_text=b'Designates weather user has self-manage access and needs onboarding guidance.'),
        ),
    ]
