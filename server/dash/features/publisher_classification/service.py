import csv
import datetime
import gzip

from django.conf import settings
from django.db import IntegrityError
from django.db.models import Case
from django.db.models import CharField
from django.db.models import Value
from django.db.models import When

from dash import models
from utils import csv_utils
from utils import metrics_compat
from utils import s3helpers
from utils import zlogging

from . import constants

logger = zlogging.getLogger(__name__)


def update_publisher_classifications_from_csv(csv_file):
    with open(csv_file, "r", encoding="utf-8") as csv_file:
        csv_dict = csv.DictReader(csv_file)
        if csv_dict.fieldnames != constants.CSV_COLUMNS:
            raise "Fields names {} are differents from {}".format(
                ", ".join(csv_dict.fieldnames), ", ".join(constants.CSV_COLUMNS)
            )
        for field in csv_dict:
            try:
                classification = models.PublisherClassification(
                    publisher=field["publisher"], category=field["category"]
                )
                classification.save()
            except IntegrityError as e:
                logger.error(e)
                continue


def update_publisher_classsifications_from_oen(date_from=None):
    date_from = date_from or datetime.datetime.now() - datetime.timedelta(days=7)
    all_publisher_classification = models.PublisherClassification.objects.all()
    new_publisher_entries = (
        models.PublisherGroupEntry.objects.filter(
            modified_dt__gte=date_from, publisher_group_id__in=constants.PUBLISHER_GROUP_CATEGORY_MAPPING.keys()
        )
        .annotate(
            category=Case(
                *[
                    When(**{"publisher_group_id": k, "then": Value(v)})
                    for k, v in constants.PUBLISHER_GROUP_CATEGORY_MAPPING.items()
                ],
                output_field=CharField(),
            )
        )
        .values("publisher", "category")
    )
    classification_to_create = new_publisher_entries.difference(
        all_publisher_classification.values("publisher", "category")
    ).values("category", "publisher")
    if not classification_to_create:
        return []
    models.PublisherClassification.objects.bulk_create(
        [models.PublisherClassification(**i) for i in classification_to_create]
    )
    return classification_to_create


def upload_publisher_classifications_to_s3():
    all_publisher_classifications = models.PublisherClassification.objects.all().values_list("publisher", "category")
    archive = gzip.compress(
        csv_utils.tuplelist_to_csv((i for i in all_publisher_classifications), dialect="excel-tab").encode()
    )
    s3 = s3helpers.S3Helper(bucket_name=settings.S3_BUCKET_B1_DATA_USE)
    try:
        s3.put(
            "/verticals/publisher_classifications_{}.gz".format(
                datetime.datetime.strftime(datetime.datetime.today(), "%y-%m-%d_%H%M")
            ),
            archive,
        )
        metrics_compat.incr("publisher_classifications_to_s3", 1, status="success")
    except Exception as e:
        metrics_compat.incr("publisher_classifications_to_s3", 1, status="failed")
        logger.exception(e)
