# Generated by Django 2.1.11 on 2020-11-02 11:35

import textwrap

from django.db import migrations

from dash.constants import EmailTemplateType


def load_data(apps, schema_editor):
    EmailTemplate = apps.get_model("dash", "EmailTemplate")

    try:
        template = EmailTemplate.objects.get(template_type=EmailTemplateType.CAMPAIGN_CLONED_SUCCESS)
    except EmailTemplate.DoesNotExist:
        template = EmailTemplate(template_type=EmailTemplateType.CAMPAIGN_CLONED_SUCCESS)
    template.subject = "Campaign “{{source_campaign_name}}” successfully cloned to “{{cloned_campaign_name}}“"
    template.body = textwrap.dedent(
        """\
        Hi,
        We’re letting you know that your campaign “{{source_campaign_name}}“ was successfully cloned to campaign “{{cloned_campaign_name}}“.
        Yours truly,
        Zemanta"""
    )
    template.save()

    try:
        template = EmailTemplate.objects.get(template_type=EmailTemplateType.CAMPAIGN_CLONED_ERROR)
    except EmailTemplate.DoesNotExist:
        template = EmailTemplate(template_type=EmailTemplateType.CAMPAIGN_CLONED_ERROR)
    template.subject = "Error cloning “{{source_campaign_name}}” to “{{cloned_campaign_name}}“"
    template.body = textwrap.dedent(
        """\
        Hi,
        We’re letting you know that there was an error cloning your campaign “{{source_campaign_name}}“ to the campaign “{{cloned_campaign_name}}“.
        {% if error_message %}
        Error: {{error_message}}.
        {% endif %}
        Yours truly,
        Zemanta"""
    )
    template.save()

    try:
        template = EmailTemplate.objects.get(template_type=EmailTemplateType.AD_GROUP_CLONED_SUCCESS)
    except EmailTemplate.DoesNotExist:
        template = EmailTemplate(template_type=EmailTemplateType.AD_GROUP_CLONED_SUCCESS)
    template.subject = "Ad group “{{source_ad_group_name}}” successfully cloned to “{{cloned_ad_group_name}}“"
    template.body = textwrap.dedent(
        """\
        Hi,
        We’re letting you know that your ad group “{{source_ad_group_name}}“ was successfully cloned to ad group “{{cloned_ad_group_name}}“.
        Yours truly,
        Zemanta"""
    )
    template.save()

    try:
        template = EmailTemplate.objects.get(template_type=EmailTemplateType.AD_GROUP_CLONED_ERROR)
    except EmailTemplate.DoesNotExist:
        template = EmailTemplate(template_type=EmailTemplateType.AD_GROUP_CLONED_ERROR)
    template.subject = "Error cloning ad group “{{source_ad_group_name}}” to “{{cloned_ad_group_name}}“"
    template.body = textwrap.dedent(
        """\
        Hi,
        We’re letting you know that there was an error cloning your ad group “{{source_ad_group_name}}“ to the ad group “{{cloned_ad_group_name}}“.
        {% if error_message %}
        Error: {{error_message}}.
        {% endif %}
        Yours truly,
        Zemanta"""
    )
    template.save()


class Migration(migrations.Migration):

    dependencies = [("dash", "0493_merge_20201022_0953")]

    operations = [migrations.RunPython(load_data)]