import logging

from django.core.management.base import BaseCommand

from automation import budgetdepletion
from utils.command_helpers import ExceptionCommand

from utils import dates_helper
import datetime
import reports
import dash.models as dm

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):
    def handle(self, *args, **options):
        logger.info('Start: Stopping and notifying depleted budget campaigns.')
        budgetdepletion.stop_and_notify_depleted_budget_campaigns()
        logger.info('Finish: Stopping and notifying depleted budget campaigns.')

        logger.info('Start: Notifying campaigns with depleting budget.')
        budgetdepletion.notify_depleting_budget_campaigns()
        logger.info('Finish: Notifying campaigns with depleting budget.')

        # EXPERIMENT TO GET YESTERDAY SPEND - REMOVE ON FEB 17.
        logger.info('getting yesterday spends')
        ad_groups = dm.AdGroup.objects.filter(id__in=[701, 1487, 1304, 1303, 1221, 1395, 1422, 1411, 1171, 1172, 1169,
                                                      1170, 1046, 885, 1498, 1499, 928, 927, 976, 1132, 1349, 1350,
                                                      836, 837, 1308])
        yesterday = datetime.date(2016, 2, 16)
        yesterday_data = reports.api_contentads.query(
            yesterday,
            yesterday,
            breakdown=['ad_group', 'source'],
            ad_group=ad_groups,
            source=[3, 4, 39]
        )

        for row in yesterday_data:
            logger.info('YESTERDAYSPENDEXPERIMENT;' +
                        str(datetime.datetime.now()) + ';' + str(yesterday) + ';' + str(row['ad_group']) + ';' +
                        str(row['source']) + ';' + str(row['billing_cost']) + ';' + str(row['media_cost']) +
                        ';' + str(row['e_media_cost']))
