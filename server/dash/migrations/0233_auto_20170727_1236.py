# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-07-27 12:36


from django.db import migrations
from dash.constants import EmailTemplateType


class Migration(migrations.Migration):

    def load_data(apps, schema_editor):
        EmailTemplate = apps.get_model('dash', 'EmailTemplate')

        template = EmailTemplate(template_type=EmailTemplateType.OEN_POSTCLICKKPI_CPA_FACTORS)
        template.subject = 'Zemanta CPA Optimization Factors'
        template.body = '''Hi OEN,

    Please find current CPA optimization factors attached.

    Yours truly,
    Zemanta'''
        template.save()

    dependencies = [
        ('dash', '0232_auto_20170727_1235'),
    ]

    operations = [
        migrations.RunPython(load_data),
    ]
