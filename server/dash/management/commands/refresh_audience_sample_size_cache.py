import influx
import logging

from utils.command_helpers import ExceptionCommand

import core.audiences
import core.models

import redshiftapi

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):

    help = "Refresh audience sample size cache"

    def add_arguments(self, parser):
        parser.add_argument("--account_id", type=int)

    @influx.timer("audiences.sample_size.cache_refresh_time")
    def handle(self, *args, **options):
        audiences = core.audiences.Audience.objects.all()

        account_id = options.get("account_id")
        if account_id:
            audiences = audiences.filter(pixel__account_id=account_id)
            logger.info("Refreshing audience sample size for account id %s", account_id)

        logger.info("About to refresh sample size cache for %s audiences", audiences.count())

        for audience in audiences:
            rules = audience.audiencerule_set.all()
            count = (
                redshiftapi.api_audiences.get_audience_sample_size(
                    audience.pixel.account.id, audience.pixel.slug, audience.ttl, rules, refresh_cache=True
                )
                * 100
            )
            count_yesterday = (
                redshiftapi.api_audiences.get_audience_sample_size(
                    audience.pixel.account.id, audience.pixel.slug, 1, rules, refresh_cache=True
                )
                * 100
            )

            logger.info(
                "Successfully refreshed sample size cache for audience id %s, count %s, count_yesterday %s",
                audience.id,
                count,
                count_yesterday,
            )
