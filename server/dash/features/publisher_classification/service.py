import csv
import datetime
import logging

from django.db import IntegrityError
from django.db.models import Case, CharField, Value, When

from dash import models

from . import constants

logger = logging.getLogger(__name__)


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


def update_publisher_classsifications_from_oen():
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    all_publisher_classification = models.PublisherClassification.objects.all()
    new_publisher_entries = (
        models.PublisherGroupEntry.objects.filter(
            modified_dt__gte=yesterday,
            publisher_group_id__in=constants.PUBLISHER_GROUP_CATEGORY_MAPPING,
            publisher__in=all_publisher_classification.values("publisher"),
        )
        .annotate(
            category=Case(
                *[
                    When(**{"publisher_group_id": k, "then": Value(v)})
                    for k, v in constants.PUBLISHER_GROUP_CATEGORY_MAPPING.items()
                ],
                output_field=CharField()
            )
        )
        .values("publisher", "category")
    )
    print(new_publisher_entries)
    classification_to_create = new_publisher_entries.difference(
        all_publisher_classification.values("publisher", "category")
    ).values("category", "publisher")
    if not classification_to_create:
        return False
    models.PublisherClassification.objects.bulk_create(
        [models.PublisherClassification(**i) for i in classification_to_create]
    )
    return classification_to_create
