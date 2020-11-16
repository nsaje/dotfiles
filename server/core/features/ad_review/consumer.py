from django.conf import settings

from utils import aletheia_kafka_consumer
from utils import zlogging

from . import realtimechanges

logger = zlogging.getLogger(__name__)

GROUP_ID = "z1-ad-status-consumer"
TOPIC = "AdChanges"


def start_consumer():
    consumer = aletheia_kafka_consumer.AletheiaKafkaConsumer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_RTB_IN, group_id=GROUP_ID, topics=[TOPIC], auto_offset_reset="latest"
    )
    consumer.map(process_notification)


def process_notification(ad_change_notification):
    try:
        if _has_status_changes(ad_change_notification):
            internal_ad_id = _extract_internal_ad_id(ad_change_notification)
            realtimechanges.ping_ad_if_relevant(internal_ad_id)
    except Exception:
        logger.exception("Exception when trying to process ad change notification", notification=ad_change_notification)


def _has_status_changes(ad_change_notification):
    if not ad_change_notification["type"] == "UPDATE":
        return False

    for change in ad_change_notification["changes"]:
        if change.get("name") == "STATUS":
            return True


def _extract_internal_ad_id(ad_change_notification):
    return ad_change_notification.get("entityProperties", {}).get("ID", {}).get("value")
