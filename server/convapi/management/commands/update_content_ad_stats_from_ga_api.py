import logging
from optparse import make_option
import datetime
import sys

from django.core.management.base import BaseCommand

from convapi import ga_api
from dash.models import GAAnalyticsAccount, Account, AdGroupSettings, ContentAd
from dash.constants import GATrackingType

from convapi.ga_api import GAApiReport
from reports import update
from reports.constants import ReportType

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-d', '--date',
                    help='Date for which Google Analytics reports need to be retrieved. Format YYYY-MM-DD',
                    dest='ga_date'),
    )

    def handle(self, *args, **options):
        try:
            ga_date = options['ga_date']
        except:
            logger.exception("Failed parsing command line arguments")
            sys.exit(1)

        if ga_date is None:
            logger.info("No date was provided. Using yesterday's date by default.")
            ga_date = datetime.date.today() - datetime.timedelta(days=1)
        else:
            ga_date = datetime.datetime.strptime(ga_date, '%Y-%m-%d').date()

        logger.info("Retrieving post click data for publisher from Google Analytics.")
        ga_service = ga_api.get_ga_service()
        ga_reports = GAApiReport(ga_service, ga_date)
        adgroup_settings_ga_api_enabled = AdGroupSettings.objects.all().group_current_settings() \
            .filter(enable_ga_tracking=True, ga_tracking_type=GATrackingType.API)
        adgroup_ga_api_enabled = [settings.ad_group for settings in adgroup_settings_ga_api_enabled]
        content_ad_ids_ga_api_enabled = set(
            ContentAd.objects.filter(ad_group__in=adgroup_ga_api_enabled).values_list('id', flat=True))
        accounts_ga_api_enabled = Account.objects.filter(campaign__adgroup__in=adgroup_ga_api_enabled).distinct()
        ga_accounts = GAAnalyticsAccount.objects.filter(account__in=accounts_ga_api_enabled)
        for ga_account in ga_accounts:
            ga_reports.download(ga_account)
        stats_ga_enabled = self._filter_stats_ga_enabled(ga_reports.entries, content_ad_ids_ga_api_enabled)
        update.process_report(ga_date, stats_ga_enabled, ReportType.GOOGLE_ANALYTICS)

    def _filter_stats_ga_enabled(self, ga_report_entries, content_ad_ids_ga_api_enabled):
        ga_stats = []
        for entry_key in ga_report_entries.keys():
            if entry_key[1] in content_ad_ids_ga_api_enabled:
                stats = ga_report_entries[entry_key]
                ga_stats.append(stats)
        return ga_stats
