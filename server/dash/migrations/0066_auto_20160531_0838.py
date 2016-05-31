# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-31 08:38
from __future__ import unicode_literals

from django.db import migrations
from dash.constants import EmailTemplateType


def load_data(apps, schema_editor):
    EmailTemplate = apps.get_model('dash', 'EmailTemplate')

    EmailTemplate(
        template_type=EmailTemplateType.ADGROUP_CHANGE,
        subject=u'Settings change - ad group {ad_group.name}, campaign {campaign.name}, account {account.name}',
        body=u'''Hi account manager of ad group {ad_group.name}

We'd like to notify you that {user.email} has made the following change in the settings of the ad group {ad_group.name}, campaign {campaign.name}, account {account.name}:

{changes_text}

Please check {link_url} for further details.

Yours truly,
Zemanta
    '''
    ).save()

    EmailTemplate(
        template_type=EmailTemplateType.CAMPAIGN_CHANGE,
        subject=u'Settings change - campaign {campaign.name}, account {account.name}',
        body='''Hi account manager of campaign {campaign.name}

We'd like to notify you that {user.email} has made the following change in the settings of campaign {campaign.name}, account {account.name}:

{changes_text}

Please check {link_url} for further details.

Yours truly,
Zemanta
    '''
    ).save()

    EmailTemplate(
        template_type=EmailTemplateType.BUDGET_CHANGE,
        subject=u'Settings change - campaign {campaign.name}, account {account.name}',
        body=u'''Hi account manager of campaign {campaign.name}

We'd like to notify you that {user.email} has made the following change in the budget of campaign {campaign.name}, account {account.name}:

{changes_text}

Please check {link_url} for further details.

Yours truly,
Zemanta
    ''').save()

    EmailTemplate(
        template_type=EmailTemplateType.PIXEL_ADD,
        subject=u'Conversion pixel added - account {account.name}',
        body=u'''Hi default account manager of {account.name},

We'd like to notify you that {user.email} has added a conversion pixel on account {account.name}. Please check {link_url} for details.

Yours truly,
Zemanta
    ''').save()

    EmailTemplate(
        template_type=EmailTemplateType.PASSWORD_RESET,
        subject='Recover Password',
        body=u'''<p>Hi {user.first_name},</p>
<p>You told us you forgot your password. If you really did, click here to choose a new one:</p>
<a href="{link_url}">Choose a New Password</a>
<p>If you didn't mean to reset your password, then you can just ignore this email; your password will not change.</p>
<p>
As always, please don't hesitate to contact help@zemanta.com with any questions.
</p>
<p>
Thanks,<br/>
Zemanta Client Services
</p>
    '''
    ).save()

    EmailTemplate(
        template_type=EmailTemplateType.NEW_USER,
        subject=u'Welcome to Zemanta!',
        body=u'''<p>Hi {user.first_name},</p>
<p>
Welcome to Zemanta's Content DSP!
</p>
<p>
We're excited to promote your quality content across our extended network. Through our reporting dashboard, you can monitor campaign performance across multiple supply channels.
</p>
<p>
Click <a href="{link_url}">here</a> to create a password to log into your Zemanta account.
</p>
<p>
As always, please don't hesitate to contact help@zemanta.com with any questions.
</p>
<p>
Thanks,<br/>
Zemanta Client Services
</p>
    ''').save()

    EmailTemplate(
        template_type=EmailTemplateType.SUPPLY_REPORT,
        subject=u'Zemanta Report for {date}',
        body=u'''
Hello,

Here are the impressions and spend for {date}.

Impressions: {impressions}
Spend: {cost}

Yours truly,
Zemanta

---
The reporting data is an estimate. Final amounts are tallied and should be invoiced per your agreement with Zemanta.
* All times are in Eastern Standard Time (EST).
    ''').save()

    EmailTemplate(
        template_type=EmailTemplateType.SCHEDULED_EXPORT_REPORT,
        subject=u'Zemanta Scheduled Report: {report_name}',
        body=u'''Hi,

Please find attached Your {frequency} scheduled report "{report_name}" for {entity_level}{entity_name}{granularity}.

Yours truly,
Zemanta

----------

Report was scheduled by {scheduled_by}.
    ''').save()

    EmailTemplate(
        template_type=EmailTemplateType.DEPLETING_BUDGET,
        subject=u'Campaign budget low - {campaign.name}, {account.name}',
        body=u'''Hi account manager of {campaign.name}

We'd like to notify you that campaign {campaign.name}, {account.name} is about to run out of available budget.

The available budget remaining today is ${available_budget}, current daily cap is ${cap} and yesterday's spend was ${yesterday_spend}.

Please check {link_url} for details.

Yours truly,
Zemanta
    ''').save()

    EmailTemplate(
        template_type=EmailTemplateType.CAMPAIGN_STOPPED,
        subject='Campaign stopped - {campaign.name}, {account.name}',
        body=u'''Hi account manager of {campaign.name}

We'd like to notify you that campaign {campaign.name}, {account.name} has run out of available budget and was stopped.

Please check {link_url} for details.

Yours truly,
Zemanta
    ''').save()


class Migration(migrations.Migration):

    dependencies = [
        ('dash', '0065_auto_20160530_1513'),
    ]

    operations = [
        migrations.RunPython(load_data)
    ]
