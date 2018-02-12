# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2017-02-16 08:06


from django.db import migrations
from dash.constants import EmailTemplateType


def load_data(apps, schema_editor):
    EmailTemplate = apps.get_model('dash', 'EmailTemplate')

    EmailTemplate(
        template_type=EmailTemplateType.PACING_NOTIFICATION,
        subject='Your campaign is {alert}',
        body='''Hi, campaign manager,

your campaign {campaign.name} ({account.name}) is {alert} with a rate of {pacing}%.

Please consider adjusting daily spend caps on ad group source settings. Visit https://one.zemanta.com/v2/analytics/campaign/{campaign.id} to get a list of all active ad groups.

Yours truly,
Zemanta'''
    ).save()


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0171_auto_20170215_1055'),
    ]

    operations = [
        migrations.RunPython(load_data)
    ]
