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

OUTBRAIN_SOURCE_ID = 3

def get_ad_group_sources():
    actions = actionlog.models.ActionLog.objects.filter(
        action_type=actionlog.constants.ActionType.MANUAL,
        state=actionlog.constants.ActionState.WAITING,
        ad_group_source__source__id=OUTBRAIN_SOURCE_ID,
        action='set_property',
        payload__contains='target_regions'
    ).select_related('ad_group_source__ad_group')

    ad_group_sources = []

    for action in actions:
        ad_group_source = action.ad_group_source
        ad_group = ad_group_source.ad_group

        ad_group_settings = ad_group.get_current_settings()
        ad_group_source_settings = ad_group_source.get_current_settings()

        if models.AdGroup.get_running_status_by_sources_setting(ad_group_settings, [ad_group_source_settings]) \
                == constants.AdGroupRunningStatus.ACTIVE:
            ad_group_sources.append(ad_group_source)

    return ad_group_sources


def get_outbrain_marketer_name(ad_group_source):
    account = ad_group_source.ad_group.campaign.account
    outbrain_account = models.OutbrainAccount.objects.get(marketer_id=account.outbrain_marketer_id)
    return outbrain_account.marketer_name if outbrain_account and outbrain_account.marketer_name else 'n/a'


class Command(ExceptionCommand):

    help = "Sends email with ad groups that had location targeting changed"

    def add_arguments(self, parser):
        parser.add_argument('--email', metavar='EMAIL', nargs='*', help='Reports receiver e-mail.',
                            default=['operations@zemanta.com', 'gregor.ratajc@zemanta.com'])

    def handle(self, *args, **options):
        set_logger_verbosity(logger, options)

        source = models.Source.objects.get(id=OUTBRAIN_SOURCE_ID)
        ad_group_sources = get_ad_group_sources(source)

        if not ad_group_sources:
            logger.info("No new location settings to configure manually")
            return

        links = []
        for ad_group_source in ad_group_sources:
            links.append(
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
            )

        body = textwrap.dedent(u"""\
        Subject: Content approvals - {date}

        Hi!

        I'd like to ask you for approval of content in the following campaigns:

        {ad_group_links}

        Thanks.

        """)

        date_str = datetime.date.today().strftime('%Y-%m-%d')
        body = body.format(
            date=date_str,
            ad_group_links=u'\n'.join(links) if links else u'(No new content)'
        )

        subject = u'Zemanta auto-generated approval email for {} {}'.format(source.name, date_str)
        email_list = options['email']

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
                logger.exception('Content approval auto-generated e-mail to %s was not sent '
                                 'because an exception was raised', email_list)
        else:
            logger.info(body)
