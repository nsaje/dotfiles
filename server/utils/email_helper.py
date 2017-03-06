import logging
import traceback
import re
from decimal import Decimal

from django.core.mail import send_mail
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.core.mail.message import EmailMessage, EmailMultiAlternatives
from django.template.loader import render_to_string

import dash.constants
import dash.models
import analytics.management_report
import analytics.client_report
import analytics.statements

from utils import pagerduty_helper
from utils import dates_helper


logger = logging.getLogger(__name__)


def prepare_recipients(email_text):
    return (email.strip() for email in email_text.split(',') if email)


def format_email(template_type, **kwargs):
    # since editing through admin is currently unavailable no validation takes
    # place
    template = dash.models.EmailTemplate.objects.get(template_type=template_type)
    return template.subject.format(**kwargs), template.body.format(**kwargs), prepare_recipients(template.recipients)


def format_template(subject, content):
    return render_to_string('email.html', {
        'subject': subject,
        'content': '<p>' + '</p><p>'.join(re.split(r'\n+', content)) + '</p>'
    })


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
    if not to_emails:
        return
    try:
        send_mail(
            subject,
            body,
            'Zemanta <{}>'.format(settings.FROM_EMAIL),
            to_emails,
            fail_silently=False,
            html_message=format_template(subject, body),
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
            event_type=pagerduty_helper.PagerDutyEventType.ENGINEERS,
            incident_key='account_manager_notification_mail_failed',
            description='Account manager email notification was not sent because '
            'an exception was raised: {}'.format(traceback.format_exc(e)),
            details=desc,
        )


def send_pacing_notification_email(campaign, emails, pacing, alert):
    subject, body, additional_emails = format_email(
        dash.constants.EmailTemplateType.PACING_NOTIFICATION,
        campaign=campaign,
        account=campaign.account,
        pacing=pacing.quantize(Decimal('.01')),
        alert=alert == 'low' and 'underpacing' or 'overpacing',
    )
    email = EmailMultiAlternatives(
        subject,
        body,
        'Zemanta <{}>'.format(settings.FROM_EMAIL),
        emails,
        bcc=additional_emails
    )
    email.attach_alternative(format_template(subject, body), "text/html")
    email.send(fail_silently=False)


def send_obj_changes_notification_email(obj, request, changes_text):
    if isinstance(obj, dash.models.AdGroup):
        send_ad_group_notification_email(obj, request, changes_text)
    elif isinstance(obj, dash.models.Campaign):
        send_campaign_notification_email(obj, request, changes_text)
    elif isinstance(obj, dash.models.Account):
        send_account_notification_email(obj, request, changes_text)
    else:
        raise Exception('Object {} (pk: {}) does not have a notification email method set'.format(obj, obj.pk))


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

    subject, body, _ = format_email(dash.constants.EmailTemplateType.ADGROUP_CHANGE, **args)
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

    subject, body, _ = format_email(dash.constants.EmailTemplateType.CAMPAIGN_CHANGE, **args)
    emails = list(set(email_manager_list(campaign)) - set([request.user.email]))
    if not emails:
        return
    send_notification_mail(
        emails, subject, body, campaign.get_campaign_url(request))


def send_account_notification_email(account, request, changes_text):
    if not should_send_account_notification_mail(account, request.user, request):
        return

    link_url = request.build_absolute_uri('/accounts/{}/history'.format(account.pk))
    link_url = link_url.replace('http://', 'https://')

    args = {
        'user': request.user,
        'account': account,
        'link_url': link_url,
        'changes_text': _format_changes_text(changes_text)
    }

    subject, body, _ = format_email(dash.constants.EmailTemplateType.ACCOUNT_CHANGE, **args)
    send_notification_mail(
        [account.get_current_settings().default_account_manager.email],
        subject, body, account.get_account_url(request))


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
    subject, body, _ = format_email(dash.constants.EmailTemplateType.BUDGET_CHANGE, **args)
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
    subject, body, _ = format_email(dash.constants.EmailTemplateType.PIXEL_ADD, **args)
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

    subject, body, _ = format_email(dash.constants.EmailTemplateType.PASSWORD_RESET, **args)
    _send_email_to_user(user, request, subject, body)


def send_email_to_new_user(user, request):
    args = {
        'user': user,
        'link_url': _generate_password_reset_url(user, request),
    }
    subject, body, _ = format_email(dash.constants.EmailTemplateType.USER_NEW, **args)
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
            html_message=format_template(subject, body)
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
            event_type=pagerduty_helper.PagerDutyEventType.ENGINEERS,
            incident_key='user_mail_failed',
            description=message,
            details=desc,
        )


def send_supply_report_email(email, date, impressions, cost, custom_subject=None, publisher_report=None):
    date = dates_helper.format_date_mmddyyyy(date)
    args = {
        'date': date,
        'impressions': impressions,
        'cost': cost,
    }
    subject, body, _ = format_email(dash.constants.EmailTemplateType.SUPPLY_REPORT, **args)
    if custom_subject:
        subject = custom_subject.format(date=date)

    try:
        email = EmailMultiAlternatives(
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
            event_type=pagerduty_helper.PagerDutyEventType.ENGINEERS,
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
            event_type=pagerduty_helper.PagerDutyEventType.ENGINEERS,
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

    subject, body, _ = format_email(dash.constants.EmailTemplateType.SCHEDULED_EXPORT_REPORT, **args)

    if not email_adresses:
        raise Exception('No recipient emails: ' + report_name)
    email = EmailMultiAlternatives(subject, body, 'Zemanta <{}>'.format(
        settings.FROM_EMAIL
    ), email_adresses)
    email.attach(report_filename + '.csv', report_contents, 'text/csv')
    email.attach_alternative(format_template(subject, body), "text/html")
    email.send(fail_silently=False)


def send_livestream_email(user, session_url):
    subject, body, recipients = format_email(
        dash.constants.EmailTemplateType.LIVESTREAM_SESSION,
        user=user,
        session_url=session_url,
    )
    email = EmailMultiAlternatives(subject, body, 'Zemanta <{}>'.format(
        settings.FROM_EMAIL
    ), recipients)
    email.attach_alternative(format_template(subject, body), "text/html")
    email.send(fail_silently=False)


def send_daily_management_report_email():
    subject, body, recipients = format_email(dash.constants.EmailTemplateType.DAILY_MANAGEMENT_REPORT)
    email = EmailMultiAlternatives(subject, body, 'Zemanta <{}>'.format(
        settings.FROM_EMAIL
    ), recipients)
    email.attach_alternative(analytics.management_report.get_daily_report_html(), "text/html")
    email.send(fail_silently=False)


def send_weekly_client_report_email():
    subject, body, recipients = format_email(dash.constants.EmailTemplateType.WEEKLY_CLIENT_REPORT)
    email = EmailMultiAlternatives(subject, body, 'Zemanta <{}>'.format(
        settings.FROM_EMAIL
    ), recipients)
    email.attach_alternative(analytics.client_report.get_weekly_report_html(), "text/html")
    email.send(fail_silently=False)


def send_weekly_inventory_report_email():
    subject, body, recipients = format_email(
        dash.constants.EmailTemplateType.WEEKLY_INVENTORY_REPORT,
        report_url=analytics.statements.generate_csv(
            'inventory-report/{}.csv'.format(str(dates_helper.local_today())),
            analytics.statements.inventory_report_csv
        )
    )
    email = EmailMultiAlternatives(subject, body, 'Zemanta <{}>'.format(
        settings.FROM_EMAIL
    ), recipients)
    email.attach_alternative(format_template(subject, body), "text/html")
    email.send(fail_silently=False)


def send_outbrain_accounts_running_out_email(n):
    subject, body, recipients = format_email(
        dash.constants.EmailTemplateType.OUTBRAIN_ACCOUNTS_RUNNING_OUT,
        n=n,
    )
    email = EmailMultiAlternatives(subject, body, 'Zemanta <{}>'.format(
        settings.FROM_EMAIL
    ), recipients)
    email.attach_alternative(format_template(subject, body), "text/html")
    email.send()


def send_ga_setup_instructions(user):
    subject, body, _ = format_email(dash.constants.EmailTemplateType.GA_SETUP_INSTRUCTIONS)
    email = EmailMultiAlternatives(subject, body, 'Zemanta <{}>'.format(
        settings.FROM_EMAIL
    ), [user.email])
    email.attach_alternative(render_to_string('ga_setup_instructions.html'), "text/html")
    email.send(fail_silently=True)


def send_async_report(
        user, recipients, report_path, start_date, end_date, expiry_date, filtered_sources,
        show_archived, show_blacklisted_publishers,
        breakdown_columns, columns, include_totals, ad_group):

    filters = []
    if show_archived:
        filters.append('Show archived items')
    if show_blacklisted_publishers != dash.constants.PublisherBlacklistFilter.SHOW_ALL:
        filters.append('Show {} publishers only'.format(
            dash.constants.PublisherBlacklistFilter.get_text(show_blacklisted_publishers).lower()))
    if filtered_sources:
        filters.extend([x.name for x in filtered_sources])

    subject, plain_body, _ = format_email(
        dash.constants.EmailTemplateType.ASYNC_REPORT_RESULTS,
        link_url=report_path,
        account_name=ad_group.campaign.account.name,
        campaign_name=ad_group.campaign.name,
        ad_group_name=ad_group.name,
        start_date=dates_helper.format_date_mmddyyyy(start_date),
        end_date=dates_helper.format_date_mmddyyyy(end_date),
        expiry_date=dates_helper.format_date_mmddyyyy(expiry_date),
        tab_name=breakdown_columns[0] if breakdown_columns else '',
        breakdown=(', '.join(breakdown_columns[1:]) if breakdown_columns else '') or '/',
        columns=', '.join(columns),
        filters=', '.join(filters) if filters else '/',
        include_totals='Yes' if include_totals else 'No',
    )

    email = EmailMultiAlternatives(subject, plain_body, 'Zemanta <{}>'.format(
        settings.FROM_EMAIL
    ), [user.email] + (recipients or []))
    email.attach_alternative(format_template(subject, plain_body), "text/html")
    email.send(fail_silently=False)


def send_depleting_credits_email(user, accounts):
    accounts_list = ''
    for account in accounts:
        accounts_list += ' - {} {}\n'.format(
            account.get_long_name(),
            'https://one.zemanta.com/accounts/{}/credit'.format(account.pk)
        )
    subject, plain_body, recipients = format_email(
        dash.constants.EmailTemplateType.DEPLETING_CREDITS,
        accounts_list=accounts_list
    )
    email = EmailMultiAlternatives(subject, plain_body, 'Zemanta <{}>'.format(
        settings.FROM_EMAIL
    ), [user.email], bcc=recipients or [])
    email.attach_alternative(format_template(subject, plain_body), "text/html")
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
