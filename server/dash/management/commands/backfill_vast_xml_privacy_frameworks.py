import requests
from django.db import transaction

import core.features.videoassets.constants
import core.features.videoassets.models
import dash.features.contentupload
from utils import zlogging
from utils.command_helpers import Z1Command
from utils.queryset_helper import chunk_iterator

logger = zlogging.getLogger(__name__)

BATCH_SIZE = 100


class Command(Z1Command):
    help = "Apply B1 browsers targeting hacks to ad groups."

    def handle(self, *args, **options):
        """
        Temporary management command to backfill videoasssets supported privacy frameworks on vast xml
        """

        self._backfill_supported_privacy_frameworks()

    def _backfill_supported_privacy_frameworks(self):
        videoasset_qs = core.features.videoassets.models.VideoAsset.objects.filter(
            type=core.features.videoassets.constants.VideoAssetType.VAST_UPLOAD
        )
        chunk_number = 0
        for videoasset_chunk in chunk_iterator(videoasset_qs, chunk_size=BATCH_SIZE):
            chunk_number += 1
            logger.info("Processing contentad chunk number %s...", chunk_number)
            with transaction.atomic():
                for videoasset in videoasset_chunk:
                    try:
                        videoasset.supported_privacy_frameworks = self._get_privacy_frameworks(
                            videoasset.get_vast_url(ready_for_use=False)
                        )
                    except requests.exceptions.RequestException:
                        videoasset.suported_privacy_frameworks = []
                        logger.info("Failed to fetch XML: {}".format(videoasset.id))

                    videoasset.save()
            logger.info("Chunk number %s processed...", chunk_number)
        logger.info("Migration of contentad trackers completed")

    def _get_privacy_frameworks(self, vast_url):
        r = requests.get(vast_url)
        if r.status_code != 200:
            raise requests.exceptions.RequestException("Invalid server response")

        return dash.features.contentupload.get_privacy_frameworks(r.content.decode("utf-8"), None)
