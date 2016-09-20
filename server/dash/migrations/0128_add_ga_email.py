# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-09-16 09:29
from __future__ import unicode_literals

from django.db import migrations
from dash.constants import EmailTemplateType


def load_data(apps, schema_editor):
    EmailTemplate = apps.get_model('dash', 'EmailTemplate')

    EmailTemplate(
        template_type=EmailTemplateType.GA_SETUP_INSTRUCTIONS,
        subject=u'Google Analytics Setup Instructions',
        body=u'''Dear manager,

the instructions on http://help.zemanta.com/article/show/10814-realtime-google-analytics-reports_1 will walk you through the simple setup process in Zemanta One and your Google Analytics account.

Yours truly,
Zemanta
    '''
    ).save()


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0127_merge'),
    ]

    operations = [
        migrations.RunPython(load_data)
    ]
