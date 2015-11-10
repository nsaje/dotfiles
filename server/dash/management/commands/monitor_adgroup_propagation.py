import logging

from django.core.management.base import BaseCommand

from dash import models
from utils import redirector_helper
from utils import statsd_helper
from utils.command_helpers import set_logger_verbosity


logger = logging.getLogger(__name__)


KEYS_TO_CHECK = ('tracking_code', 'enable_ga_tracking', 'enable_adobe_tracking', 'adobe_tracking_param')


class Command(BaseCommand):

    help = "Checks and posts ad group propagation consistency between R1 and Z1."

    def add_arguments(self, parser):
        parser.add_argument('--adgroups', metavar='ADGROUPS', nargs='+',
                            help='A list of Ad Group IDs. Separated with spaces.')
        parser.add_argument('--send-stats', metavar='SEND_STATS', action='store_true')

    def handle(self, *args, **options):
        ad_group_ids = options['adgroups']
        set_logger_verbosity(logger, options)

        logger.info('Checking ad group propagation consistency between Z1 and R1')

        ad_groups = models.AdGroup.objects.all()
        if ad_group_ids:
            logger.info('Narrowing to user defined ad group selection')
            ad_groups = ad_groups.filter(pk__in=ad_group_ids)

        nr_exceptions = 0
        nr_not_synced = 0
        for ad_group in ad_groups:

            ad_group_settings = ad_group.get_current_settings()
            if not ad_group_settings:
                logger.warning('Ad group %s does not have settings', ad_group.pk)
                continue

            if ad_group_settings.archived:
                # if ad group was specifically selected than let it through
                if not ad_group_ids or ad_group.pk not in ad_group_ids:
                    continue

            try:
                redirector_adgroup_data = redirector_helper.get_adgroup(ad_group.pk)
            except Exception as e:
                logger.exception('Cannot retrieve ad group settings from redirector for ad group %d', ad_group.pk, e)
                nr_exceptions += 1

            ad_group_settings_dict = ad_group_settings.get_settings_dict()

            diff = []
            for diff_key in KEYS_TO_CHECK:
                if redirector_adgroup_data.get(diff_key) != ad_group_settings_dict.get(diff_key):
                    diff.append(diff_key)

            if diff:
                nr_not_synced += 1
                logger.warning('Ad group %s is not synced, differing keys %s', ad_group.pk, diff)

        if options['send_stats']:
            statsd_helper.statsd_gauge('propagation_consistency.ad_group_r1.exceptions', nr_exceptions)
            statsd_helper.statsd_gauge('propagation_consistency.ad_group_r1.not_in_sync', nr_not_synced)
