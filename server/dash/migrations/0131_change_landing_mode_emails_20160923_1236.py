# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-09-23 12:36


from django.db import migrations
from dash.constants import EmailTemplateType


def load_data(apps, schema_editor):
    EmailTemplate = apps.get_model('dash', 'EmailTemplate')

    landing_mode_swith_template = EmailTemplate.objects.get(template_type=EmailTemplateType.CAMPAIGN_LANDING_MODE_SWITCH)
    landing_mode_swith_template.body = '''Hi, campaign manager,

your campaign {campaign.name} ({account.name}) has been switched to automated landing mode because it is approaching the budget limit.

Please visit {link_url} and assign additional budget, if you don’t want campaign to be switched to the landing mode. While campaign is in landing mode, CPCs and daily budgets of media sources will not be available for any changes, to ensure accurate delivery.

Learn more about landing mode: http://help.zemanta.com/article/show/12922-campaign-stop-with-landing-mode.

Yours truly,
Zemanta'''
    landing_mode_swith_template.save()

    budget_low_template = EmailTemplate.objects.get(template_type=EmailTemplateType.CAMPAIGN_BUDGET_LOW)
    budget_low_template.body = '''Hi, campaign manager,

your campaign {campaign.name} ({account.name}) will soon run out of budget.

Please add the budget to continue to adjust media sources settings by your needs, if you don’t want campaign to end in a few days. To do so please visit {link_url} and assign budget to your campaign.

If you don’t take any actions, system will automatically turn on the landing mode to hit your budget. While campaign is in landing mode, CPCs and daily budgets of media sources will not be available for any changes. Learn more about landing mode: http://help.zemanta.com/article/show/12922-campaign-stop-with-landing-mode.

Yours truly,
Zemanta'''
    budget_low_template.save()


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0130_auto_20160920_1354'),
    ]

    operations = [
        migrations.RunPython(load_data)
    ]
