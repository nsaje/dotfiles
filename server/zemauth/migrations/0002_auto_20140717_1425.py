# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zemauth', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL('ALTER TABLE zemauth_user DROP CONSTRAINT zemauth_user_email_key;'),
        migrations.RunSQL('CREATE UNIQUE INDEX zemauth_user_email_idx ON zemauth_user (lower(email));')
    ]
