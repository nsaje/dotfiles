import datetime
import logging
import textwrap

from django.conf import settings
from django.core.mail import send_mail

from dash import constants
from dash import models
from utils.command_helpers import ExceptionCommand
from utils.command_helpers import set_logger_verbosity
from utils.url_helper import get_full_z1_url

logger = logging.getLogger(__name__)

DEFAULT_EMAIL_RECIPIENTS = ["zem-operations@outbrain.com", "prodops@outbrain.com"]


class Command(ExceptionCommand):

    help = "Sends email listing Outbrain pending manual actions"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email", metavar="EMAIL", nargs="*", default=DEFAULT_EMAIL_RECIPIENTS, help="Reports receiver e-mail."
        )

    def handle(self, *args, **options):
        set_logger_verbosity(logger, options)

        subject, body = get_content_submission_content()

        if not body:
            logger.info("No new content.")
            return

        send_emails(options["email"], subject, body)


OUTBRAIN_SOURCE_ID = 3
SUBJECT_CONTENT_APPROVALS = "Zemanta auto-generated approval email for Outbrain {}"
BODY_CONTENT_APPROVALS = textwrap.dedent(
    """\
        Subject: Content approvals - {date}

        Hi!

        I'd like to ask you for approval of content in the following campaigns:

        {content}

        Thanks.

        """
)


def get_content_submission_content():
    ad_group_sources = get_ad_group_sources_with_content_submission_pending()
    if not ad_group_sources:
        return None, None

    content = [get_campaign_name(ad_group_source) for ad_group_source in ad_group_sources]
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    subject = SUBJECT_CONTENT_APPROVALS.format(date_str)
    body = BODY_CONTENT_APPROVALS.format(date=date_str, content="\n".join(content))
    return subject, body


def get_ad_group_sources_with_content_submission_pending():
    ad_group_ids = (
        models.ContentAdSource.objects.filter(
            source__id=OUTBRAIN_SOURCE_ID,
            content_ad__archived=False,
            submission_status=constants.ContentAdSubmissionStatus.PENDING,
        )
        .values_list("content_ad__ad_group_id", flat=True)
        .distinct()
    )

    ad_group_ids = (
        models.AdGroup.objects.filter(pk__in=ad_group_ids)
        .exclude_archived()
        .filter_active()
        .values_list("pk", flat=True)
    )

    ad_group_sources = (
        models.AdGroupSource.objects.filter(source__id=OUTBRAIN_SOURCE_ID)
        .filter(ad_group__in=ad_group_ids)
        .filter_active()
        .select_related("ad_group")
    )

    return ad_group_sources


def get_campaign_name(ad_group_source):
    return "{name} / {marketer_name} / {one_dash_url} / {supply_dash_url}".format(
        name=ad_group_source.get_external_name(),
        marketer_name=get_outbrain_marketer_name(ad_group_source),
        one_dash_url=get_full_z1_url("/v2/analytics/adgroup/{}/sources".format(ad_group_source.ad_group_id)),
        supply_dash_url=get_full_z1_url(ad_group_source.get_supply_dash_url()),
    )


def get_outbrain_marketer_name(ad_group_source):
    account = ad_group_source.ad_group.campaign.account
    outbrain_account = models.OutbrainAccount.objects.filter(marketer_id=account.outbrain_marketer_id).first()
    return outbrain_account.marketer_name if outbrain_account and outbrain_account.marketer_name else "n/a"


def send_emails(email_list, subject, body):
    if email_list:
        try:
            send_mail(subject, body, "Zemanta <{}>".format(settings.FROM_EMAIL), email_list, fail_silently=False)
        except Exception:
            logger.exception(
                "Outbrain pending %s auto-generated e-mail was not sent " "because an exception was raised", email_list
            )
    else:
        logger.info(body)
