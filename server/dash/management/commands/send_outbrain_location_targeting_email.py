import datetime
import logging
import textwrap

from django.conf import settings
from django.core.mail import send_mail

import actionlog.models
import actionlog.constants

from dash import models
from dash import constants
from utils.command_helpers import set_logger_verbosity, ExceptionCommand
from utils.url_helper import get_full_z1_url

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):

    help = "Sends email with ad groups that had location targeting changed"

    def add_arguments(self, parser):
        parser.add_argument('--email', metavar='EMAIL', nargs='*', help='Reports receiver e-mail.',
                            default=['operations@zemanta.com', 'gregor.ratajc@zemanta.com'])
        parser.add_argument('--action', metavar='ACTION', nargs=1, default=None,
                            help='Manual action to be sent. Possible values: location_targeting, content_approval.')

    def handle(self, *args, **options):
        set_logger_verbosity(logger, options)

        content_type = options['action']
        if content_type == 'location_targeting':
            subject, body = get_location_targeting_content()
            if not body:
                logger.info("No new location targeting settings to configure.")
                return
        elif content_type == 'content_approval':
            subject, body = get_content_submission_content()
            if not body:
                logger.info("No new content to approve.")
                return
        else:
            logger.exception('Unrecognized action type.', type)
            return

        send_emails(content_type, options['email'], subject, body)


OUTBRAIN_SOURCE_ID = 3
SUBJECT_CONTENT_APPROVALS = u'Zemanta auto-generated approval email for Outbrain {}'
BODY_CONTENT_APPROVALS = textwrap.dedent(u"""\
        Subject: Content approvals - {date}

        Hi!

        I'd like to ask you for approval of content in the following campaigns:

        {content}

        Thanks.

        """)

SUBJECT_LOCATION_TARGETING = u'Zemanta auto-generated DMA/State targeting email for Outbrain {}'
BODY_LOCATION_TARGETING = textwrap.dedent(u"""\
        Subject: DMA/State targeting  - {date}

        Hi!

        I'd like to ask you to set following location targetings:

        {content}

        Thanks.

        """)


def get_location_targeting_content():
    location_targeting_settings = get_pending_location_targeting_settings()
    if not location_targeting_settings:
        return None, None

    content = []
    for setting, ad_group_sources in location_targeting_settings.iteritems():
        campaign_names = [get_campaign_name(ad_group_source) for ad_group_source in ad_group_sources]
        content.append(textwrap.dedent(u"""\
        {location_targeting}

        for the campaigns:

        {campaign_name}
        """).format(
                location_targeting=setting,
                campaign_name=campaign_names.join('\n')
            )
        )
    date_str = datetime.date.today().strftime('%Y-%m-%d')
    subject = SUBJECT_LOCATION_TARGETING.format(date_str)
    body = BODY_LOCATION_TARGETING.format(
        date=date_str,
        content=u'\n\n'.join(content) if content else u'(No new content)'
    )
    return subject, body


def get_content_submission_content():
    ad_group_sources = get_ad_group_sources_with_content_submission_pending()
    if not ad_group_sources:
        return None, None

    content = [get_campaign_name(ad_group_source) for ad_group_source in ad_group_sources]
    date_str = datetime.date.today().strftime('%Y-%m-%d')
    subject = SUBJECT_CONTENT_APPROVALS.format(date_str)
    body = BODY_CONTENT_APPROVALS.format(
        date=date_str,
        content=u'\n'.join(content) if content else u'(No new content)'
    )
    return subject, body


def get_pending_location_targeting_settings():
    actions = actionlog.models.ActionLog.objects.filter(
        action_type=actionlog.constants.ActionType.MANUAL,
        state=actionlog.constants.ActionState.WAITING,
        ad_group_source__source__id=OUTBRAIN_SOURCE_ID,
        action='set_property',
        payload__contains='target_regions'
    ).select_related('ad_group_source__ad_group')

    target_regions_settings = {}
    for action in actions:
        ad_group_source = action.ad_group_source
        ad_group = ad_group_source.ad_group
        if is_ad_group_source_active(ad_group, ad_group_source):
            setting = action.payload['value']
            if setting not in target_regions_settings:
                target_regions_settings[setting] = []
            target_regions_settings[setting].append(ad_group_source)
    return actions


def get_ad_group_sources_with_content_submission_pending():
    ad_group_ids = models.ContentAdSource.objects.filter(
        source__id=OUTBRAIN_SOURCE_ID,
        submission_status=constants.ContentAdSubmissionStatus.PENDING
    ).values('content_ad__ad_group_id').distinct()

    ad_group_sources = []
    for ad_group_id_dict in ad_group_ids:
        ad_group_id = ad_group_id_dict['content_ad__ad_group_id']
        ad_group = models.AdGroup.objects.get(pk=ad_group_id)
        ad_group_source = models.AdGroupSource.objects.get(ad_group=ad_group, source__id=OUTBRAIN_SOURCE_ID)
        if is_ad_group_source_active(ad_group, ad_group_source):
            ad_group_sources.append(ad_group_source)

    return ad_group_sources


def is_ad_group_source_active(ad_group, ad_group_source):
    ad_group_settings = ad_group.get_current_settings()
    ad_group_source_settings = ad_group_source.get_current_settings()
    if models.AdGroup.get_running_status_by_sources_setting(ad_group_settings, [ad_group_source_settings]) \
            == constants.AdGroupRunningStatus.ACTIVE:
        return True
    return False


def get_campaign_name(ad_group_source):
    u"{name} / {marketer_name} / {one_dash_url} / {supply_dash_url}".format(
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
    outbrain_account = models.OutbrainAccount.objects.get(marketer_id=account.outbrain_marketer_id)
    return outbrain_account.marketer_name if outbrain_account and outbrain_account.marketer_name else 'n/a'


def send_emails(content_type, email_list, subject, body):
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
            logger.exception('Outbrain pending %s auto-generated e-mail to %s was not sent '
                             'because an exception was raised', content_type, email_list)
    else:
        logger.info(body)


