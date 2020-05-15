# Generated by Django 2.1.11 on 2020-05-07 11:35

import textwrap

from django.db import migrations

from dash.constants import EmailTemplateType


def load_data(apps, schema_editor):
    EmailTemplate = apps.get_model("dash", "EmailTemplate")

    EmailTemplate(
        template_type=EmailTemplateType.CAMPAIGN_CLONED_SUCCESS,
        subject="Campaign “{{source_campaign_name}}” successfully cloned to {{cloned_campaign_name}}",
        body=textwrap.dedent(
            """\
        Hi,
        We’re letting you know that your campaign "{{source_campaign_name}}" was successfully cloned to campaign {{cloned_campaign_name}}.
        Yours truly,
        Zemanta"""
        ),
    ).save()

    EmailTemplate(
        template_type=EmailTemplateType.CAMPAIGN_CLONED_ERROR,
        subject="Error cloning “{{source_campaign_name}}” to {{cloned_campaign_name}}",
        body=textwrap.dedent(
            """\
        Hi,
        We’re letting you know that there was an error cloning your campaign "{{source_campaign_name}}" to the campaign {{cloned_campaign_name}}.
        Yours truly,
        Zemanta"""
        ),
    ).save()


class Migration(migrations.Migration):

    dependencies = [("dash", "0460_auto_20200507_1135")]

    operations = [migrations.RunPython(load_data)]