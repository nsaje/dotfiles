import logging
from optparse import make_option
import datetime
import sys

from django.core.management.base import BaseCommand

from convapi import ga_api
from dash.models import GAAnalyticsAccount, Account, AdGroupSettings
from dash.constants import GATrackingType

from convapi.ga_api import GAApiReport

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
        accounts = Account.objects.filter(campaign__adgroup__settings__enable_ga_tracking=True,
                                          campaign__adgroup__settings__ga_tracking_type=GATrackingType.API)
        for account in accounts:
            ga_api_adgroup_settings = AdGroupSettings.objects.filter(ad_group__campaign__account=account) \
                .group_current_settings() \
                .filter(enable_ga_tracking=True, ga_tracking_type=GATrackingType.API)
            ga_api_adgroup_ids = {setting.ad_group_id for setting in ga_api_adgroup_settings}
            ga_accounts = GAAnalyticsAccount.objects.filter(account=account)
            for ga_account in ga_accounts:
                ga_reports.download(ga_account)
                # TODO: filter out stats for all the ad groups that are not in ga_api_adgroup_ids
