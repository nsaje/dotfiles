import logging
import traceback

from django.core.mail import send_mail
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.core.mail.message import EmailMessage

from utils import pagerduty_helper

logger = logging.getLogger(__name__)


def send_notification_mail(account_manager, subject, body, settings_url):
    try:
        send_mail(
            subject,
            body,
            'Zemanta <{}>'.format(settings.FROM_EMAIL),
            [account_manager.email],
            fail_silently=False
        )
    except Exception as e:
        logger.exception('Account manager email notification was not sent because an exception was raised')

        desc = {
            'settings_url': settings_url
        }
        pagerduty_helper.trigger(
            event_type=pagerduty_helper.PagerDutyEventType.SYSOPS,
            incident_key='account_manager_notification_mail_failed',
            description='Account manager email notification was not sent because an exception was raised: {}'.format(traceback.format_exc(e)),
            details=desc,
        )


def send_ad_group_notification_email(ad_group, request):
    if not should_send_notification_mail(ad_group.campaign, request.user, request):
        return

    subject = u'Settings change - ad group {}, campaign {}, account {}'.format(
        ad_group.name,
        ad_group.campaign.name,
        ad_group.campaign.account.name
    )

    link_url = request.build_absolute_uri('/ad_groups/{}/agency'.format(ad_group.pk))
    link_url = link_url.replace('http://', 'https://')

    body = u'''Hi account manager of {ad_group.name}

We'd like to notify you that {user.email} has made a change in the settings of the ad group {ad_group.name}, campaign {campaign.name}, account {account.name}. Please check {link_url} for details.

Yours truly,
Zemanta
    '''
    body = body.format(
        user=request.user,
        ad_group=ad_group,
        campaign=ad_group.campaign,
        account=ad_group.campaign.account,
        link_url=link_url
    )

    campaign_settings = ad_group.campaign.get_current_settings()

    send_notification_mail(
        campaign_settings.account_manager, subject, body, ad_group.campaign.get_campaign_url(request))


def send_campaign_notification_email(campaign, request):
    if not should_send_notification_mail(campaign, request.user, request):
        return

    subject = u'Settings change - campaign {}, account {}'.format(
        campaign.name,
        campaign.account.name
    )

    link_url = request.build_absolute_uri('/campaigns/{}/agency'.format(campaign.pk))
    link_url = link_url.replace('http://', 'https://')

    body = u'''Hi account manager of {campaign.name}

We'd like to notify you that {user.email} has made a change in the settings or budget of campaign {campaign.name}, account {account.name}. Please check {link_url} for details.

Yours truly,
Zemanta
    '''
    body = body.format(
        user=request.user,
        campaign=campaign,
        account=campaign.account,
        link_url=link_url
    )

    campaign_settings = campaign.get_current_settings()

    send_notification_mail(
        campaign_settings.account_manager, subject, body, campaign.get_campaign_url(request))


def send_account_pixel_notification(account, request):
    if not should_send_account_notification_mail(account, request.user, request):
        return

    subject = u'Conversion pixel added - account {}'.format(account.name)

    link_url = request.build_absolute_uri('/accounts/{}/agency'.format(account.pk))
    link_url = link_url.replace('http://', 'https://')

    body = u'''Hi default account manager of {account.name},

We'd like to notify you that {user.email} has added a conversion pixel on account {account.name}. Please check {link_url} for details.

Yours truly,
Zemanta
    '''
    body = body.format(
        user=request.user,
        account=account,
        link_url=link_url
    )

    account_settings = account.get_current_settings()

    send_notification_mail(
        account_settings.default_account_manager, subject, body, account.get_account_url(request))


def send_password_reset_email(user, request):
    body = u'''<p>Hi {name},</p>
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

    body = body.format(
        name=user.first_name,
        link_url=_generate_password_reset_url(user, request)
    )

    _send_email_to_user(user, request, 'Recover Password', body)


def send_email_to_new_user(user, request):
    body = u'''<p>Hi {name},</p>
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
    '''

    body = body.format(
        name=user.first_name,
        link_url=_generate_password_reset_url(user, request)
    )

    return _send_email_to_user(user, request, 'Welcome to Zemanta!', body)


def _generate_password_reset_url(user, request):
    encoded_id = urlsafe_base64_encode(str(user.pk))
    token = default_token_generator.make_token(user)

    url = request.build_absolute_uri(
        reverse('set_password', args=(encoded_id, token))
    )

    return url.replace('http://', 'https://')


def _send_email_to_user(user, request, subject, body):
    try:
        send_mail(
            subject,
            body,
            'Zemanta <{}>'.format(settings.FROM_EMAIL),
            [user.email],
            fail_silently=False,
            html_message=body
        )
    except Exception as e:
        if user is None:
            message = 'Email for user was not sent because exception was raised: {}'.format(
                traceback.format_exc(e))
            desc = {}
        else:
            message = 'Email for user {} ({}) was not sent because an exception was raised: {}'.format(
                user.get_full_name(),
                user.email,
                traceback.format_exc(e)
            )

            user_url = request.build_absolute_uri(
                reverse('admin:zemauth_user_change', args=(user.pk,))
            )
            user_url = user_url.replace('http://', 'https://')

            desc = {
                'user_url': user_url
            }

        logger.error(message)

        pagerduty_helper.trigger(
            event_type=pagerduty_helper.PagerDutyEventType.SYSOPS,
            incident_key='user_mail_failed',
            description=message,
            details=desc,
        )


def send_supply_report_email(email, date, impressions, cost):
    date_str = '%d/%d/%d' % (date.month, date.day, date.year)
    subject = u'Zemanta Report for {}'.format(date_str)
    body = u'''
Hello,

Here are the impressions and spend for {date}.

Impressions: {impressions}
Spend: {cost}

Yours truly,
Zemanta

---
The reporting data is an estimate. Final amounts are tallied and should be invoiced per your agreement with Zemanta.
* All times are in Eastern Standard Time (EST).
    '''
    body = body.format(
        date=date_str,
        impressions=impressions,
        cost=cost
    )

    try:
        send_mail(
            subject,
            body,
            'Zemanta <{}>'.format(settings.SUPPLY_REPORTS_FROM_EMAIL),
            [email],
            fail_silently=False
        )
    except Exception as e:
        logger.error('Supply report e-mail to %s was not sent because an exception was raised: %s', email, traceback.format_exc(e))


def should_send_account_notification_mail(account, user, request):
    if not settings.SEND_NOTIFICATION_MAIL:
        return False

    account_settings = account.get_current_settings()

    if not account_settings or not account_settings.default_account_manager:
        logger.error(
            'Could not send e-mail because there is no default account manager set for account with id %s.',
            account.pk
        )

        desc = {
            'settings_url': account.get_campaign_url(request)
        }
        pagerduty_helper.trigger(
            event_type=pagerduty_helper.PagerDutyEventType.ADOPS,
            incident_key='notification_mail_failed',
            description='E-mail notification was not sent because default account manager is not set.',
            details=desc,
        )
        return False

    if user.pk == account_settings.default_account_manager.pk:
        return False

    return True


def should_send_notification_mail(campaign, user, request):
    if not settings.SEND_NOTIFICATION_MAIL:
        return False

    campaign_settings = campaign.get_current_settings()

    if not campaign_settings or not campaign_settings.account_manager:
        logger.error(
            'Could not send e-mail because there is no account manager set for campaign with id %s.',
            campaign.pk
        )

        desc = {
            'settings_url': campaign.get_campaign_url(request)
        }
        pagerduty_helper.trigger(
            event_type=pagerduty_helper.PagerDutyEventType.ADOPS,
            incident_key='notification_mail_failed',
            description='E-mail notification was not sent because account manager is not set.',
            details=desc,
        )
        return False

    if user.pk == campaign_settings.account_manager.pk:
        return False

    return True


def send_scheduled_export_report(report_name, frequency, granularity, entity_name, scheduled_by, email_adresses, report_contents, report_filename):
    subject = u'Zemanta Scheduled Report: {}'.format(
        report_name
    )
    body = u'''Hi,

Please find attached Your {frequency} scheduled report {report_name} for {entity_name} by {granularity}.

Report was scheduled by {scheduled_by}.

Yours truly,
Zemanta
    '''
    body = body.format(
        report_name=report_name,
        frequency=frequency.lower(),
        granularity=granularity,
        entity_name=entity_name,
        scheduled_by=scheduled_by
    )
    if not email_adresses:
        raise Exception('No recipient emails: ' + report_name)
    email = EmailMessage(subject, body, 'Zemanta <{}>'.format(settings.FROM_EMAIL), email_adresses)
    email.attach(report_filename + '.csv', report_contents, 'text/csv')
    email.send(fail_silently=False)
