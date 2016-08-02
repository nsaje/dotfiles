import datetime
import logging
import textwrap

from django.conf import settings
from django.core.mail import send_mail

from dash import models
from dash import constants
from utils.command_helpers import set_logger_verbosity, ExceptionCommand
from utils.url_helper import get_full_z1_url

logger = logging.getLogger(__name__)

DEFAULT_EMAIL_RECIPIENTS = ['operations@zemanta.com', 'gregor.ratajc@zemanta.com', 'jure.polutnik@zemanta.com']


class Command(ExceptionCommand):

    help = "Sends email listing Outbrain pending manual actions"

    def add_arguments(self, parser):
        parser.add_argument('--email', metavar='EMAIL', nargs='*', default=DEFAULT_EMAIL_RECIPIENTS,
                            help='Reports receiver e-mail.')

    def handle(self, *args, **options):
        set_logger_verbosity(logger, options)

        subject, body = get_content_submission_content()

        if not body:
            logger.info("No new content.")
            return

        send_emails(options['email'], subject, body)


OUTBRAIN_SOURCE_ID = 3
SUBJECT_CONTENT_APPROVALS = u'Zemanta auto-generated approval email for Outbrain {}'
BODY_CONTENT_APPROVALS = textwrap.dedent(u"""\
        Subject: Content approvals - {date}

        Hi!

        I'd like to ask you for approval of content in the following campaigns:

        {content}

        Thanks.

        """)


def get_content_submission_content():
    ad_group_sources = get_ad_group_sources_with_content_submission_pending()
    if not ad_group_sources:
        return None, None

    content = [get_campaign_name(ad_group_source) for ad_group_source in ad_group_sources]
    date_str = datetime.date.today().strftime('%Y-%m-%d')
    subject = SUBJECT_CONTENT_APPROVALS.format(date_str)
    body = BODY_CONTENT_APPROVALS.format(
        date=date_str,
        content=u'\n'.join(content)
    )
    return subject, body


def get_ad_group_sources_with_content_submission_pending():
    ad_group_ids = models.ContentAdSource.objects.filter(
        source__id=OUTBRAIN_SOURCE_ID,
        submission_status=constants.ContentAdSubmissionStatus.PENDING
    ).values_list('content_ad__ad_group_id', flat=True).distinct()

    ad_group_sources = models.AdGroupSource.objects\
        .filter(source__id=OUTBRAIN_SOURCE_ID)\
        .filter(ad_group__in=ad_group_ids)\
        .select_related('ad_group')

    return [ad_group_source for ad_group_source in ad_group_sources if is_ad_group_source_active(ad_group_source)]


def is_ad_group_source_active(ad_group_source):
    ad_group_settings = ad_group_source.ad_group.get_current_settings()
    ad_group_source_settings = ad_group_source.get_current_settings()
    if models.AdGroup.get_running_status_by_sources_setting(ad_group_settings, [ad_group_source_settings]) \
            == constants.AdGroupRunningStatus.ACTIVE:
        return True
    return False


def get_campaign_name(ad_group_source):
    return u"{name} / {marketer_name} / {one_dash_url} / {supply_dash_url}".format(
        name=ad_group_source.get_external_name(),
        marketer_name=get_outbrain_marketer_name(ad_group_source),
        one_dash_url=get_full_z1_url(
            '/ad_groups/{}/sources'.format(ad_group_source.ad_group_id)
        ),
        supply_dash_url=get_full_z1_url(
            ad_group_source.get_supply_dash_url()
        )
    )


def get_outbrain_marketer_name(ad_group_source):
    account = ad_group_source.ad_group.campaign.account
    outbrain_account = models.OutbrainAccount.objects.filter(marketer_id=account.outbrain_marketer_id).first()
    return outbrain_account.marketer_name if outbrain_account and outbrain_account.marketer_name else 'n/a'


def send_emails(email_list, subject, body):
    if email_list:
        try:
            send_mail(
                subject,
                body,
                'Zemanta <{}>'.format(settings.FROM_EMAIL),
                email_list,
                fail_silently=False
            )
        except Exception:
            logger.exception('Outbrain pending %s auto-generated e-mail was not sent '
                             'because an exception was raised', email_list)
    else:
        logger.info(body)
