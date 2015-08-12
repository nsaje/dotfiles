import logging
import traceback

from django.core.mail import send_mail
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode

from utils import pagerduty_helper

logger = logging.getLogger(__name__)


def send_ad_group_settings_change_email(user, account_manager, request, ad_group, campaign_url):
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
        user=user,
        ad_group=ad_group,
        campaign=ad_group.campaign,
        account=ad_group.campaign.account,
        link_url=link_url
    )

    try:
        send_mail(
            subject,
            body,
            'Zemanta <{}>'.format(settings.FROM_EMAIL),
            [account_manager.email],
            fail_silently=False
        )
    except Exception as e:
        logger.error('E-mail notification for ad group settings (ad group id: %d) change was not sent because an exception was raised: %s', ad_group.pk, traceback.format_exc(e))

        desc = {
            'campaign_settings_url': campaign_url
        }
        pagerduty_helper.trigger(
            event_type=pagerduty_helper.PagerDutyEventType.SYSOPS,
            incident_key='ad_group_settings_change_mail_failed',
            description='E-mail notification for ad group settings change was not sent because an exception was raised: {}'.format(traceback.format_exc(e)),
            details=desc,
        )


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


def send_ad_group_settings_change_mail_if_necessary(ad_group, user, request):
    if not settings.SEND_AD_GROUP_SETTINGS_CHANGE_MAIL:
        return

    campaign_settings = ad_group.campaign.get_current_settings()

    if not campaign_settings or not campaign_settings.account_manager:
        logger.error('Could not send e-mail because there is no account manager set for campaign with id %s.', ad_group.campaign.pk)

        desc = {
            'campaign_settings_url': ad_group.campaign.get_campaign_url(request)
        }
        pagerduty_helper.trigger(
            event_type=pagerduty_helper.PagerDutyEventType.ADOPS,
            incident_key='ad_group_settings_change_mail_failed',
            description='E-mail notification for ad group settings change was not sent because the campaign settings or account manager is not set.',
            details=desc,
        )
        return

    if user.pk == campaign_settings.account_manager.pk:
        return

    send_ad_group_settings_change_email(
        user,
        campaign_settings.account_manager,
        request,
        ad_group,
        ad_group.campaign.get_campaign_url(request)
    )
