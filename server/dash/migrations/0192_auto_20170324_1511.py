# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-24 15:11
from __future__ import unicode_literals

from django.db import migrations
from dash.constants import EmailTemplateType


def load_data(apps, schema_editor):
    EmailTemplate = apps.get_model('dash', 'EmailTemplate')

    template = EmailTemplate.objects.get(template_type=EmailTemplateType.NEW_DEVICE_LOGIN)
    template.subject = u'New login to Zemanta One from {browser} on {os}'
    template.body = u'''Hi,

We noticed you logged into Zemanta using {browser} on {os} on {time} from {city}, {country}.

Note: Your location may be inaccurate since it was estimated using your IP address.

If this wasn’t you your account may have been compromised. We suggest you change your password on {reset_password_url}.

If this was you no action is required.

Yours truly,
Zemanta'''
    template.save()


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0191_auto_20170324_1459'),
    ]

    operations = [
        migrations.RunPython(load_data),
    ]
