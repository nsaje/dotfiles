import logging
from optparse import make_option
import datetime
import httplib2
import sys
from apiclient.discovery import build
from oauth2client.client import SignedJwtAssertionCredentials
from django.conf import settings
from django.core.management.base import BaseCommand
from dash.models import GAAnalyticsAccount, AdGroup, ContentAd, Source
from dash.constants import GATrackingType

from convapi.ga_api import GAApiReport

logger = logging.getLogger(__name__)

GA_API_NAME = 'analytics'
GA_API_VERSION = 'v3'
GA_SCOPE = ['https://www.googleapis.com/auth/analytics.readonly']


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

        self._delete_old_stats(ga_date)
        logger.info("Retrieving post click data for publisher from Google Analytics.")
        ga_service = self._get_ga_service()
        ga_accounts = GAAnalyticsAccount.objects.filter(account__campaign__adgroup__settings__enable_ga_tracking=True,
                                                        account__campaign__adgroup__settings__ga_tracking_type=GATrackingType.API)
        for ga_account in ga_accounts:
            ga_reports = GAApiReport(ga_service, ga_account, ga_date)
            ga_reports.download()

    def _get_ga_service(self):
        logger.debug('Getting Google Analytics service.')
        credentials = SignedJwtAssertionCredentials(
            settings.GA_CLIENT_EMAIL,
            settings.GA_PRIVATE_KEY,
            GA_SCOPE
        )
        http = credentials.authorize(httplib2.Http())
        # Build the GA service object.
        service = build(GA_API_NAME, GA_API_VERSION, http=http)
        return service

    # def _update_postclick_stats(self, ga_date, ga_service, profiles):
    #     has_more = True
    #     start_index = 1
    #     while has_more:
    #         data = ga_service.data().ga().get(
    #             ids='ga:' + profiles['items'][0]['id'],
    #             start_date=ga_date.strftime('%Y-%m-%d'),
    #             end_date=ga_date.strftime('%Y-%m-%d'),
    #             metrics='ga:sessions,ga:newUsers,ga:bounceRate,ga:pageviews,ga:timeonsite',
    #             dimensions='ga:landingPagePath,ga:deviceCategory',
    #             filters='ga:landingPagePath=@_z1_',
    #             start_index=start_index
    #         ).execute()
    #         if data['totalResults'] == 0:
    #             logger.debug('No postclick data was found.')
    #             break
    #         rows = data.get('rows')
    #         for row in rows:
    #             logger.debug('Processing GA postclick data row: %s', row)
    #             content_ad_id = re.search('.*_z1_caid=(\d+)[&]?.*', row[0]).group(1)
    #             media_source_tracking_slug = re.search('.*_z1_msid=([\w-]+)[&]?.*', row[0]).group(1)
    #             self._update_postclick_item(ga_date, content_ad_id, media_source_tracking_slug, row)
    #         has_more = ((start_index + data['itemsPerPage']) < data['totalResults'])
    #         start_index += data['itemsPerPage']
    #
    # def _update_postclick_item(self, stat_date, content_ad_id, media_source_tracking_slug, row):
    #     try:
    #         content_ad = ContentAd.objects.get(pk=content_ad_id)
    #         source = Source.objects.get(tracking_slug=media_source_tracking_slug)
    #         postclick_stat, created = ContentAdPostclickStats.objects.get_or_create(date=stat_date,
    #                                                                                 content_ad=content_ad,
    #                                                                                 source=source,
    #                                                                                 defaults={
    #                                                                                     'visits': 0,
    #                                                                                     'new_visits': 0,
    #                                                                                     'bounced_visits': 0,
    #                                                                                     'pageviews': 0,
    #                                                                                     'total_time_on_site': 0
    #                                                                                 })
    #         visits = int(row[2])
    #         postclick_stat.visits += visits
    #         postclick_stat.new_visits += int(row[3])
    #         postclick_stat.bounced_visits += int(visits * float(row[4]) / 100.0)
    #         postclick_stat.pageviews += int(row[5])
    #         postclick_stat.total_time_on_site += int(float(row[6]))
    #         postclick_stat.save()
    #     except Exception as e:
    #         logger.warning('Post-click stat updating failed %s', e.message)
    #         return None
    #
    # def _update_goal_conversion_stats(self, ga_date, ga_service, profiles):
    #     profile = profiles['items'][0]
    #     goals = ga_service.management().goals().list(accountId=profile['accountId'],
    #                                                  webPropertyId=profile['webPropertyId'],
    #                                                  profileId=profile['id']).execute()
    #     for sub_goals in list_chunker(goals['items'], MAX_METRICS_PER_GA_REQUEST / NUM_METRICS_PER_GOAL):
    #         ga_metrics = self._generate_ga_metrics(sub_goals)
    #         has_more = True
    #         start_index = 1
    #         while has_more:
    #             data = ga_service.data().ga().get(
    #                 ids='ga:' + profile['id'],
    #                 start_date=ga_date.strftime('%Y-%m-%d'),
    #                 end_date=ga_date.strftime('%Y-%m-%d'),
    #                 metrics=ga_metrics,
    #                 dimensions='ga:landingPagePath,ga:deviceCategory',
    #                 filters='ga:landingPagePath=@_z1_',
    #                 start_index=start_index
    #             ).execute()
    #             if data['totalResults'] == 0:
    #                 logger.debug('No goal conversion data was found.')
    #                 break
    #             rows = data.get('rows')
    #             for row in rows:
    #                 logger.debug('Processing GA conversion goal data row: %s', row)
    #                 for i, sub_goal in enumerate(sub_goals):
    #                     content_ad_id = re.search('.*_z1_caid=(\d+)[&]?.*', row[0]).group(1)
    #                     media_source_tracking_slug = re.search('.*_z1_msid=([\w-]+)[&]?.*', row[0]).group(1)
    #                     self._update_goal_conversion_item(ga_date, content_ad_id,
    #                                                       media_source_tracking_slug,
    #                                                       sub_goal['name'],
    #                                                       row[3 + i * NUM_METRICS_PER_GOAL])
    #                 has_more = ((start_index + data['itemsPerPage']) < data['totalResults'])
    #                 start_index += data['itemsPerPage']
    #
    # def _generate_ga_metrics(self, goals):
    #     # we have to split the Google Analytics' metrics into chunks, because Google Analytics
    #     # supports at most 10 metrics per request.
    #     goal_ids = [goal['id'] for goal in goals]
    #     ga_metrics = ['ga:goal{0}ConversionRate,ga:goal{0}Completions'.format(goal_id) for goal_id in goal_ids]
    #     return ','.join(ga_metrics)
    #
    # def _update_goal_conversion_item(self, stat_date, content_ad_id, media_source_tracking_slug, goal_name,
    #                                  conversions):
    #     try:
    #         content_ad = ContentAd.objects.get(pk=content_ad_id)
    #         source = Source.objects.get(tracking_slug=media_source_tracking_slug)
    #         goal_conversion_stat, created = ContentAdGoalConversionStats.objects.get_or_create(date=stat_date,
    #                                                                                            content_ad=content_ad,
    #                                                                                            source=source,
    #                                                                                            goal_type=ReportType.GOOGLE_ANALYTICS,
    #                                                                                            goal_name=goal_name,
    #                                                                                            defaults={
    #                                                                                                'conversions': 0})
    #         goal_conversion_stat.conversions += int(conversions)
    #         goal_conversion_stat.save()
    #     except Exception as e:
    #         logger.warning('Goal Conversion stat creation failed %s', e.message)
    #         return None
