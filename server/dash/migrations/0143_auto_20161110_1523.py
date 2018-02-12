# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-11-10 15:23


from django.db import migrations
from dash.constants import EmailTemplateType


def load_data(apps, schema_editor):
    EmailTemplate = apps.get_model('dash', 'EmailTemplate')

    EmailTemplate(
        template_type=EmailTemplateType.ASYNC_REPORT_RESULTS,
        subject='Report results',
        body='''Hi {user.first_name},</p>

The report you requested is available at the following url: {link_url}.

Yours truly,
Zemanta
    '''
    ).save()


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0142_auto_20161110_1522'),
    ]

    operations = [
        migrations.RunPython(load_data)
    ]
