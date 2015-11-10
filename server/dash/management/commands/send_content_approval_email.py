import datetime
import logging
import textwrap

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.mail import send_mail

from dash import models
from dash import constants
from utils.command_helpers import set_logger_verbosity
from utils.url_helper import get_full_z1_url


logger = logging.getLogger(__name__)


def get_ad_group_sources(source):
    ad_group_ids = models.ContentAdSource.objects.filter(
        source=source,
        submission_status=constants.ContentAdSubmissionStatus.PENDING
    ).values_list('content_ad__ad_group_id', flat=True)

    return models.AdGroupSource.objects.filter(ad_group_id__in=ad_group_ids, source=source)


class Command(BaseCommand):

    help = "Sends email with ad groups that had content ads added recently"

    def add_arguments(self, parser):
        parser.add_argument('--email', metavar='EMAIL', nargs='*', help='Reports receiver e-mail.',
                            default=['dusan.omercevic@zemanta.com', 'gregor.ratajc@zemanta.com'])
        parser.add_argument('--source-id', metavar='SOURCEID', nargs='?', default='3', type=int,
                            help='Source id. 3 (Outbrain) by default.')

    def handle(self, *args, **options):
        set_logger_verbosity(logger, options)

        source = models.Source.objects.get(id=options['source_id'])
        ad_group_sources = get_ad_group_sources(source)

        links = []
        for ad_group_source in ad_group_sources:
            links.append(
                "{name} / {one_dash_url} / {supply_dash_url}".format(
                    name=ad_group_source.get_external_name(),
                    one_dash_url=get_full_z1_url(
                        '/ad_groups/{}/sources'.format(ad_group_source.ad_group_id)
                    ),
                    supply_dash_url=get_full_z1_url(
                        ad_group_source.get_supply_dash_url()
                    )
                )
            )

        body = textwrap.dedent("""\
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
            ad_group_links='\n'.join(links)
        )

        subject = 'Zemanta auto-generated approval email for {} {}'.format(source.name, date_str)
        email = options['email']

        if email:
            try:
                send_mail(
                    subject,
                    body,
                    'Zemanta <{}>'.format(settings.FROM_EMAIL),
                    [email],
                    fail_silently=False
                )
            except Exception:
                logger.exception('Content approval auto-generated e-mail to %s was not sent '
                                 'because an exception was raised', email)
        else:
            logger.info(body)
