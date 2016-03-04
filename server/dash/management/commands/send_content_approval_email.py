import sys
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


def get_ad_group_sources(source):
    ad_group_ids = models.ContentAdSource.objects.filter(
        source=source,
        submission_status=constants.ContentAdSubmissionStatus.PENDING
    ).values('content_ad__ad_group_id').distinct()

    ad_group_sources = []

    for ad_group_id_dict in ad_group_ids:
        ad_group_id = ad_group_id_dict['content_ad__ad_group_id']

        ad_group = models.AdGroup.objects.get(pk=ad_group_id)
        ad_group_settings = ad_group.get_current_settings()
        ad_group_source = models.AdGroupSource.objects.get(ad_group=ad_group, source=source)
        ad_group_source_settings = ad_group_source.get_current_settings()

        if models.AdGroup.get_running_status_by_sources_setting(ad_group_settings, [ad_group_source_settings])\
           == constants.AdGroupRunningStatus.ACTIVE:
            ad_group_sources.append(ad_group_source)

    return ad_group_sources


class Command(ExceptionCommand):

    help = "Sends email with ad groups that had content ads added recently"

    def add_arguments(self, parser):
        parser.add_argument('--email', metavar='EMAIL', nargs='*', help='Reports receiver e-mail.',
                            default=['operations@zemanta.com', 'gregor.ratajc@zemanta.com'])
        parser.add_argument('--source-id', metavar='SOURCEID', nargs='?', default='3', type=int,
                            help='Source id. 3 (Outbrain) by default.')

    def handle(self, *args, **options):
        set_logger_verbosity(logger, options)

        source = models.Source.objects.get(id=options['source_id'])
        ad_group_sources = get_ad_group_sources(source)

        if not ad_group_sources:
            logger.info("No new content to approve")
            return

        links = []
        for ad_group_source in ad_group_sources:
            links.append(
                u"{name} / {one_dash_url} / {supply_dash_url}".format(
                    name=ad_group_source.get_external_name(),
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

        Best regards,

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
