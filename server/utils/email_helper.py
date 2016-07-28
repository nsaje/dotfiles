import logging
import traceback

from django.core.mail import send_mail
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.core.mail.message import EmailMessage, EmailMultiAlternatives

from dash.constants import EmailTemplateType
import dash.models
import reports.management_report

from utils import pagerduty_helper

logger = logging.getLogger(__name__)

# TODO: move this somewhere appropriate
OPERATIONS_EMAILS = ['operations@zemanta.com', 'ziga.stopinsek@zemanta.com']
MANAGEMENT_EMAILS = ['ziga.stopinsek@zemanta.com', 'bostjan@zemanta.com', 'urska.kosec@zemanta.com']


def format_email(template_type, **kwargs):
    # since editing through admin is currently unavailable no validation takes
    # place
    template = dash.models.EmailTemplate.objects.get(template_type=template_type)
    return template.subject.format(**kwargs), template.body.format(**kwargs)


def email_manager_list(campaign):
    '''
    Fetch campaign manager and account manager emails if they exist
    '''
    campaign_manager = campaign.get_current_settings().campaign_manager
    account_manager = campaign.account.get_current_settings().default_account_manager
    ret = set([])
    if account_manager is not None:
        ret.add(account_manager.email)
    if campaign_manager is not None:
        ret.add(campaign_manager.email)
    return list(ret)


def send_notification_mail(to_emails, subject, body, settings_url=None):
    try:
        send_mail(
            subject,
            body,
            'Zemanta <{}>'.format(settings.FROM_EMAIL),
            to_emails,
            fail_silently=False
        )
    except Exception as e:
        logger.exception(
            'Account manager email notification was not sent because '
            'an exception was raised'
        )

        desc = {}
        if settings_url:
            desc['settings_url'] = settings_url

        pagerduty_helper.trigger(
            event_type=pagerduty_helper.PagerDutyEventType.SYSOPS,
            incident_key='account_manager_notification_mail_failed',
            description='Account manager email notification was not sent because '
            'an exception was raised: {}'.format(traceback.format_exc(e)),
            details=desc,
        )


def send_ad_group_notification_email(ad_group, request, changes_text):
    if not should_send_notification_mail(ad_group.campaign, request.user, request):
        return

    link_url = request.build_absolute_uri('/ad_groups/{}/history'.format(ad_group.pk))
    link_url = link_url.replace('http://', 'https://')
    args = {
        'user': request.user,
        'ad_group': ad_group,
        'campaign': ad_group.campaign,
        'account': ad_group.campaign.account,
        'link_url': link_url,
        'changes_text': _format_changes_text(changes_text)
    }

    subject, body = format_email(EmailTemplateType.ADGROUP_CHANGE, **args)
    emails = list(set(email_manager_list(ad_group.campaign)) - set([request.user.email]))
    if not emails:
        return
    send_notification_mail(
        emails, subject, body, ad_group.campaign.get_campaign_url(request))


def send_campaign_notification_email(campaign, request, changes_text):
    if not should_send_notification_mail(campaign, request.user, request):
        return

    link_url = request.build_absolute_uri('/campaigns/{}/history'.format(campaign.pk))
    link_url = link_url.replace('http://', 'https://')

    args = {
        'user': request.user,
        'campaign': campaign,
        'account': campaign.account,
        'link_url': link_url,
        'changes_text': _format_changes_text(changes_text)
    }

    subject, body = format_email(EmailTemplateType.CAMPAIGN_CHANGE, **args)
    emails = list(set(email_manager_list(campaign)) - set([request.user.email]))
    if not emails:
        return
    send_notification_mail(
        emails, subject, body, campaign.get_campaign_url(request))


def send_budget_notification_email(campaign, request, changes_text):
    if not should_send_notification_mail(campaign, request.user, request):
        return

    link_url = request.build_absolute_uri('/campaigns/{}/history'.format(campaign.pk))
    link_url = link_url.replace('http://', 'https://')
    args = {
        'user': request.user,
        'campaign': campaign,
        'account': campaign.account,
        'link_url': link_url,
        'changes_text': _format_changes_text(changes_text),
    }
    subject, body = format_email(EmailTemplateType.BUDGET_CHANGE, **args)
    emails = list(set(email_manager_list(campaign)) - set([request.user.email]))
    if not emails:
        return
    send_notification_mail(
        emails, subject, body, campaign.get_campaign_url(request))


def send_account_pixel_notification(account, request):
    if not should_send_account_notification_mail(account, request.user, request):
        return
    link_url = request.build_absolute_uri('/accounts/{}/settings'.format(account.pk))
    link_url = link_url.replace('http://', 'https://')
    args = {
        'user': request.user,
        'account': account,
        'link_url': link_url
    }
    subject, body = format_email(EmailTemplateType.PIXEL_ADD, **args)
    account_settings = account.get_current_settings()

    send_notification_mail(
        [account_settings.default_account_manager.email],
        subject,
        body,
        account.get_account_url(request)
    )


def send_password_reset_email(user, request):
    args = {
        'user': user,
        'link_url': _generate_password_reset_url(user, request),
    }

    subject, body = format_email(EmailTemplateType.PASSWORD_RESET, **args)
    _send_email_to_user(user, request, subject, body)


def send_email_to_new_user(user, request):
    args = {
        'user': user,
        'link_url': _generate_password_reset_url(user, request),
    }
    subject, body = format_email(EmailTemplateType.USER_NEW, **args)
    return _send_email_to_user(user, request, subject, body)


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
            message =\
                'Email for user {} ({}) was not sent because an exception was raised: {}'.format(
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


def send_supply_report_email(email, date, impressions, cost, publisher_report=None):
    date_str = '%d/%d/%d' % (date.month, date.day, date.year)
    args = {
        'date': date_str,
        'impressions': impressions,
        'cost': cost,
    }
    subject, body = format_email(EmailTemplateType.SUPPLY_REPORT, **args)

    try:
        email = EmailMessage(
            subject,
            body,
            'Zemanta <{}>'.format(settings.SUPPLY_REPORTS_FROM_EMAIL),
            [email]
        )
        if publisher_report:
            email.attach('publisher_report.csv', publisher_report, 'text/csv')

        email.send(fail_silently=False)
    except Exception as e:
        logger.error(
            'Supply report e-mail to %s was not sent because an exception was raised: %s',
            email,
            traceback.format_exc(e))


def should_send_account_notification_mail(account, user, request):
    if not settings.SEND_NOTIFICATION_MAIL:
        return False

    account_settings = account.get_current_settings()

    if not account_settings or not account_settings.default_account_manager:
        logger.error(
            'Could not send e-mail because there is no default account '
            'manager set for account with id %s.',
            account.pk
        )

        desc = {
            'settings_url': account.get_account_url(request)
        }
        pagerduty_helper.trigger(
            event_type=pagerduty_helper.PagerDutyEventType.ADOPS,
            incident_key='notification_mail_failed',
            description='E-mail notification was not sent because '
            'default account manager is not set.',
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

    if not campaign_settings or not campaign_settings.campaign_manager:
        logger.error(
            'Could not send e-mail because there is no account manager '
            'set for campaign with id %s.',
            campaign.pk
        )

        desc = {
            'settings_url': campaign.get_campaign_url(request)
        }
        pagerduty_helper.trigger(
            event_type=pagerduty_helper.PagerDutyEventType.ADOPS,
            incident_key='notification_mail_failed',
            description='E-mail notification was not sent because '
            'account manager is not set.',
            details=desc,
        )
        return False

    if user.pk == campaign_settings.campaign_manager.pk:
        return False

    return True


def send_scheduled_export_report(report_name, frequency, granularity,
                                 entity_level, entity_name, scheduled_by,
                                 email_adresses, report_contents, report_filename):
    args = {
        'frequency': frequency.lower(),
        'report_name': report_name,
        'entity_level': entity_level,
        'entity_name': ' ' + entity_name if entity_name != entity_level else '',
        'granularity': ' by ' + granularity if granularity != entity_level else '',
        'scheduled_by': scheduled_by,
    }

    subject, body = format_email(EmailTemplateType.SCHEDULED_EXPORT_REPORT, **args)

    if not email_adresses:
        raise Exception('No recipient emails: ' + report_name)
    email = EmailMessage(subject, body, 'Zemanta <{}>'.format(
        settings.FROM_EMAIL
    ), email_adresses)
    email.attach(report_filename + '.csv', report_contents, 'text/csv')
    email.send(fail_silently=False)


def send_livestream_email(user, session_url):
    subject, body = format_email(
        EmailTemplateType.LIVESTREAM_SESSION,
        user=user,
        session_url=session_url,
    )
    email = EmailMessage(subject, body, 'Zemanta <{}>'.format(
        settings.FROM_EMAIL
    ), OPERATIONS_EMAILS)
    email.send(fail_silently=False)


def send_daily_management_report_email():
    # TODO: use email template
    subject = 'Zemanta One daily management report'
    email = EmailMultiAlternatives(subject, '', 'Zemanta <{}>'.format(
        settings.FROM_EMAIL
    ), MANAGEMENT_EMAILS)
    email.attach_alternative(reports.management_report.get_daily_report_html(), "text/html")
    email.send(fail_silently=False)


def _format_changes_text(changes_text):
    lines = changes_text.split('\n')
    for i in range(len(lines)):
        lines[i] = '- ' + lines[i]

        # remove end punctuations
        if lines[i][-1] in '.,':
            lines[i] = lines[i][:-1]

        # append the right punctuation
        lines[i] += '.' if (i + 1) == len(lines) else ','

    return '\n'.join(lines)
