# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2017-02-10 09:40


from django.db import migrations
from dash.constants import EmailTemplateType


def load_data(apps, schema_editor):
    EmailTemplate = apps.get_model('dash', 'EmailTemplate')
    EmailTemplate(
        template_type=EmailTemplateType.DEPLETING_CREDITS,
        subject='Depleting credit line items',
        body='''Dear sales representative,

Following accounts have depleting credit line items:
{accounts_list}

Yours truly,
Zemanta
    '''
    ).save()


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0168_accountsettings_salesforce_url'),
    ]

    operations = [
        migrations.RunPython(load_data)
    ]
