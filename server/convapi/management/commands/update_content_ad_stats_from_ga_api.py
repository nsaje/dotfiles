import logging
from optparse import make_option
import datetime
import sys

from django.core.management.base import BaseCommand

from convapi import ga_api
from dash.models import GAAnalyticsAccount, Account, AdGroupSettings, ContentAd
from dash.constants import GATrackingType

from convapi.ga_api import GAApiReport
from reports import refresh
from reports import update
from reports.constants import ReportType
from utils.command_helpers import parse_date, ExceptionCommand

logger = logging.getLogger(__name__)

SOURCE_Z1 = 'z1'


class Command(ExceptionCommand):
    option_list = BaseCommand.option_list + (
        make_option('--from_date', help='Iso format (YYYY-MM-DD).', default=None),
        make_option('--to_date', help='Iso format (YYYY-MM-DD).', default=None),
    )

    def handle(self, *args, **options):
        from_date = parse_date(options, 'from_date')
        to_date = parse_date(options, 'to_date')

        if not from_date:
            from_date = datetime.date.today() - datetime.timedelta(days=1)

        if not to_date:
            to_date = datetime.date.today() - datetime.timedelta(days=1)

        ga_service = ga_api.get_ga_service()
        ga_accounts, content_ads = self._get_ga_accounts_and_content_ads()
        date = from_date
        while date <= to_date:
            logger.info("Retrieving post click data for publisher from Google Analytics for date %s.", date)
            self._fetch_reports(ga_service, from_date, ga_accounts, content_ads)
            date += datetime.timedelta(days=1)

    def _get_ga_accounts_and_content_ads(self):
        adgroup_settings_ga_api_enabled = [current_settings for current_settings in
                                           AdGroupSettings.objects.all().group_current_settings() if
                                           current_settings.enable_ga_tracking and
                                           current_settings.ga_tracking_type == GATrackingType.API]

        adgroup_ga_api_enabled = [settings.ad_group for settings in adgroup_settings_ga_api_enabled]
        content_ad_ids_ga_api_enabled = set(
            ContentAd.objects.filter(ad_group__in=adgroup_ga_api_enabled).values_list('id', flat=True))
        accounts_ga_api_enabled = Account.objects.filter(campaign__adgroup__in=adgroup_ga_api_enabled).distinct()
        ga_accounts = GAAnalyticsAccount.objects.filter(account__in=accounts_ga_api_enabled)
        return ga_accounts, content_ad_ids_ga_api_enabled

    def _fetch_reports(self, service, date, ga_accounts, content_ads):
        ga_reports = GAApiReport(service, date)
        for ga_account in ga_accounts:
            ga_reports.download(ga_account)
        stats_ga_enabled = self._filter_valid_stats(ga_reports.get_content_ad_stats(), content_ads)
        update.process_report(date, stats_ga_enabled, ReportType.GOOGLE_ANALYTICS)
        refresh.put_pub_postclick_stats_to_s3(date, ga_reports.get_publisher_stats(), "ga_api")

    def _filter_valid_stats(self, ga_report_entries, content_ad_ids_ga_api_enabled):
        ga_stats = []
        for entry in ga_report_entries:
            # filter out the GA entries that came from Z1 (i.e. one of the Zemanta employees clicked the link) and
            # the entries that belong to content ad grops that aren't configured to receive stats via GA API
            if entry.source_param == SOURCE_Z1 or entry.content_ad_id not in content_ad_ids_ga_api_enabled:
                continue

            ga_stats.append(entry)

        return ga_stats
