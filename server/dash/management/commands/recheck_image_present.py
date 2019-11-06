import datetime
from concurrent.futures import ThreadPoolExecutor

import boto3
import botocore.exceptions

import core.models
from utils import zlogging
from utils.command_helpers import Z1Command

logger = zlogging.getLogger(__name__)


NUM_WORKERS = 20

config = botocore.config.Config(max_pool_connections=NUM_WORKERS)
s3 = boto3.resource("s3", config=config)


class Command(Z1Command):
    help = "Re-check that ads have images present"

    def add_arguments(self, parser):
        parser.add_argument("--with-false-positives", action="store_true")

    def handle(self, *args, **options):
        if options.get("with_false_positives"):
            logger.info("Checking false positives...")
            self.recheck(image_present=True)

        logger.info("Checking false negatives...")
        self.recheck(image_present=False)

    def recheck(self, image_present):
        image_ids = list(
            core.models.ContentAd.objects.filter(
                image_present=image_present, created_dt__lt=datetime.datetime(2019, 4, 30)
            )
            .exclude(ad_group__campaign__account_id__in=[305, 293])
            .values_list("image_id", flat=True)
            .distinct("image_id")
        )

        self.total = len(image_ids)
        logger.info("Checking for %s images" % self.total)

        self.count = 0
        with ThreadPoolExecutor(max_workers=NUM_WORKERS) as thread_pool:
            results = thread_pool.map(self._is_image_present, image_ids)

        image_ids_unexpected = []
        for res in results:
            if not image_present and res[1] is True:
                logger.info("Found new image %s!" % res[0])
                image_ids_unexpected.append(res[0])
            if image_present and res[1] is False:
                logger.info("Image %s missing!" % res[0])
                image_ids_unexpected.append(res[0])

        if image_ids_unexpected:
            logger.warning("Images recheck: %s images' presence differs from expectations" % len(image_ids_unexpected))

            with open("image_present_%s.csv" % (not image_present), "w") as f:
                for image_id in image_ids_unexpected:
                    f.write(image_id)
                    f.write("\n")

            logger.info("Updating image_present flag in DB")
            core.models.ContentAd.objects.filter(image_id__in=image_ids_unexpected).update(
                image_present=(not image_present)
            )
        logger.info("All images OK")

    def _is_image_present(self, image_id):
        self.count += 1
        if self.count % 1000 == 0:
            logger.info("Processing image %s/%s" % (self.count, self.total))
        try:
            s3.Object("zemthumbnailer", image_id + ".jpg").load()
        except botocore.exceptions.ClientError:
            return (image_id, False)
        except Exception:
            return (image_id, None)
        return (image_id, True)
