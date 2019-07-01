import logging

from dash import models
from utils import redirector_helper
from utils.command_helpers import Z1Command

logger = logging.getLogger(__name__)


class Command(Z1Command):
    def handle(self, *args, **options):
        for pixel_traffic in redirector_helper.get_pixel_traffic():
            logger.info("Updating pixel: slug: %s, account: %s", pixel_traffic["slug"], pixel_traffic["accountid"])

            try:
                pixel = models.ConversionPixel.objects.get(
                    slug=pixel_traffic["slug"], account_id=pixel_traffic["accountid"]
                )

                pixel.last_triggered = pixel_traffic["lasttriggered"]
                pixel.impressions = pixel_traffic["impressions"]
                pixel.save()
            except models.ConversionPixel.DoesNotExist:
                logger.info("Pixel traffic for non existent pixel: %s", pixel_traffic)
