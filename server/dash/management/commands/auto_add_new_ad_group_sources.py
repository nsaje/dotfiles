import logging
from utils.command_helpers import ExceptionCommand
from core.features.source_adoption import auto_add_new_ad_group_sources

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):
    help = "Add source to ad groups of accounts which have automatic addition of newly released sources turned on."

    def add_arguments(self, parser):
        parser.add_argument("source_id", type=int)

    def handle(self, *args, **options):
        released_on, not_released_on = auto_add_new_ad_group_sources(options.get("source_id"), logger)
        retargeting_msg = "Not available on {} ad groups due to retargeting not supported or source not allowed.".format(
            not_released_on
        )
        logger.info(
            "Source available on {} ad groups. {}".format(released_on, retargeting_msg if not_released_on else "")
        )
