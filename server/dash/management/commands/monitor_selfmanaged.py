import datetime
import logging
import influx

from django.core.management.base import BaseCommand

import dash.constants
import dash.models

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        logger.info('Monitor self-managed actions in history and user action log.')

        hour_ago = datetime.datetime.utcnow() - datetime.timedelta(hours=1)

        history_sf_count = dash.models.History.objects.all().filter(
            created_dt__gte=hour_ago,
            created_by__email__isnull=False
        ).exclude(
            created_by__email__icontains="@zemanta"
        ).exclude(
            created_by__is_test_user=True
        ).exclude(
            action_type__isnull=True
        ).count()

        influx.gauge('dash.self_managed_actions.history', history_sf_count)

        ual_sf_count = dash.models.UserActionLog.objects.all().filter(
            created_dt__gte=hour_ago,
            created_by__email__isnull=False
        ).exclude(
            created_by__email__icontains="@zemanta"
        ).exclude(
            created_by__is_test_user=True
        ).count()

        influx.gauge('dash.self_managed_actions.ualog', ual_sf_count)
