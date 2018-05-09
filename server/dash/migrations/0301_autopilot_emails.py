# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-05-07 12:15
from __future__ import unicode_literals

from django.db import migrations
from dash.constants import EmailTemplateType

from textwrap import dedent


def load_data(apps, schema_editor):
    EmailTemplate = apps.get_model('dash', 'EmailTemplate')
    try:
        template = EmailTemplate.objects.get(template_type=EmailTemplateType.AUTOPILOT_CAMPAIGN_BUDGET_INIT)
    except EmailTemplate.DoesNotExist:
        template = EmailTemplate(
            subject='Campaign put on budget optimization - {{ account.name }}',
            template_type=EmailTemplateType.AUTOPILOT_CAMPAIGN_BUDGET_INIT,
        )
    body = '''Hi Manager of {{ account.name }}

        Budget optimization settings on Your campaign {{ campaign.name }} have been changed.
        System made the following changes:
        {% for c in changes %}
        AdGroup: {{ c.adgroup.name }} ({{ c.history_url }})
        {% endfor %}

        - all Paused Media Sources' Daily Spend Caps have been set to minimum values.

        Please check {{ link_url }} for details.

        Yours truly,
        Zemanta
    '''
    template.body = dedent(body)
    template.save()

    try:
        template = EmailTemplate.objects.get(template_type=EmailTemplateType.AUTOPILOT_CAMPAIGN_CHANGE)
    except EmailTemplate.DoesNotExist:
        template = EmailTemplate(
            subject='Campaign budget optimization Changes - {{ campaign.name }}, {{ account.name }}',
            template_type=EmailTemplateType.AUTOPILOT_CAMPAIGN_CHANGE,
        )
    body = '''Hi Manager of {{ account.name }}

        In campaign {{ campaign.name }}, which is set to budget optimization, the system made the following changes:

        {% for c in changes %}
        AdGroup: {{ c.adgroup.name }} ({{ c.history_url }})
        {% if 'media_sources' in c and c.media_sources and 'media_sources_url' in c %}
        To improve ad group\'s performance, please consider pausing the following media sources: {{ c.media_sources|join:", " }}.
        ({{ c.media_sources_url }})
        {% endif %}
        {% endfor %}

        Please check {{ link_url }} for details.

        Yours truly,
        Zemanta
    '''
    template.body = dedent(body)
    template.save()

    try:
        template = EmailTemplate.objects.get(template_type=EmailTemplateType.AUTOPILOT_AD_GROUP_BUDGET_INIT)
    except EmailTemplate.DoesNotExist:
        template = EmailTemplate(
            subject='Ad Group put on Autopilot - {{ account.name }}',
            template_type=EmailTemplateType.AUTOPILOT_AD_GROUP_BUDGET_INIT,
        )
    body = '''Hi Manager of {{ account.name }}

        Autopilot's settings on Your ad group in campaign {{ campaign.name }} have been changed.
        Autopilot made the following changes:

        {% for c in changes %}
        AdGroup: {{ c.adgroup.name }} ({{ c.history_url }})
        {% endfor %}

        - all Paused Media Sources' Daily Budgets have been set to minimum values.

        Please check {{ link_url }} for details.

        Yours truly,
        Zemanta
    '''
    template.body = dedent(body)
    template.save()

    try:
        template = EmailTemplate.objects.get(template_type=EmailTemplateType.AUTOPILOT_AD_GROUP_CHANGE)
    except EmailTemplate.DoesNotExist:
        template = EmailTemplate(
            subject='Campaign Autopilot Changes - {{ campaign.name }}, {{ account.name }}',
            template_type=EmailTemplateType.AUTOPILOT_AD_GROUP_CHANGE,
        )
    body = '''Hi Manager of {{ account.name }}

        On the ad groups in campaign {{campaign.name}}, which are set to autopilot, the system made the following changes:

        {% for c in changes %}
        AdGroup: {{ c.adgroup.name }} ({{ c.history_url }})
        {% if 'media_sources' in c and c.media_sources and 'media_sources_url' in c %}
        To improve ad group\'s performance, please consider pausing the following media sources: {{ c.media_sources|join:", " }}.
        ({{ c.media_sources_url }})
        {% endif %}
        {% endfor %}

        Please check {{ link_url }} for details.

        Yours truly,
        Zemanta
    '''
    template.body = dedent(body)
    template.save()


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0300_email_template_rendering'),
    ]

    operations = [
        migrations.RunPython(load_data)
    ]
