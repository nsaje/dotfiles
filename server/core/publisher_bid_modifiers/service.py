import numbers
import csv
import random
import string
import os

import io as StringIO
from utils import s3helpers
from django.db import transaction
from django.conf import settings
from dash import models

from . import exceptions
from .publisher_bid_modifier import PublisherBidModifier

MODIFIER_MAX = 11.0
MODIFIER_MIN = 0.0


def get(ad_group):
    return [
        {"publisher": item.publisher, "source": item.source, "modifier": item.modifier}
        for item in PublisherBidModifier.objects.filter(ad_group=ad_group).select_related("source").order_by("pk")
    ]


@transaction.atomic
def set(ad_group, publisher, source, modifier):
    if not modifier:
        _delete(ad_group, source, publisher)
        return

    if not isinstance(modifier, numbers.Number) or not MODIFIER_MIN <= modifier <= MODIFIER_MAX:
        raise exceptions.BidModifierInvalid

    _update_or_create(ad_group, source, publisher, modifier)


def _delete(ad_group, source, publisher):
    PublisherBidModifier.objects.filter(ad_group=ad_group, source=source, publisher=publisher).delete()


def _update_or_create(ad_group, source, publisher, modifier):
    PublisherBidModifier.objects.update_or_create(
        defaults={"modifier": modifier}, ad_group=ad_group, source=source, publisher=publisher
    )


def make_csv_error_file(entries, csv_columns, ad_group_id):
    csv_error_file = StringIO.StringIO()
    csv_error_writer = csv.DictWriter(csv_error_file, csv_columns, extrasaction="ignore")
    csv_error_writer.writeheader()
    csv_error_writer.writerows(entries)

    csv_error_content = csv_error_file.getvalue()
    csv_error_key = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(64))

    s3_helper = s3helpers.S3Helper(settings.S3_BUCKET_PUBLISHER_GROUPS)
    s3_helper.put(
        os.path.join("publisher_bid_modifier_errors", "ad_group_{}".format(ad_group_id), csv_error_key + ".csv"),
        csv_error_content,
    )

    return csv_error_key


def clean_entries(entries):
    cleaned_entries = []
    has_error = False
    sources_by_slug = {x.get_clean_slug(): x for x in models.Source.objects.all()}

    for entry in entries:
        errors = []

        modifier = _clean_bid_modifier(entry["Bid Modifier"], errors)
        source = _clean_source_slug(entry["Source Slug"], sources_by_slug, errors)
        publisher = _clean_publisher(entry["Publisher"], errors)

        # We don't add 'all publishers' row to cleaned entries.
        if entry["Publisher"] == "all publishers":
            if entry["Bid Modifier"] != "":
                errors.append("'all publishers' can not have a bid modifier set")
        else:
            cleaned_entries.append({"modifier": modifier, "publisher": publisher, "source": source})

        if errors:
            entry["Errors"] = "; ".join(errors)
            has_error = True

    return cleaned_entries, has_error


def _clean_bid_modifier(modifier, errors):
    if modifier == "":
        modifier = 1.0

    try:
        modifier = float(modifier)
    except ValueError:
        errors.append("Invalid Bid Modifier")
        return None

    if modifier < 0.01:
        errors.append("Bid modifier too low (< 0.01)")

    if modifier > 11.0:
        errors.append("Bid modifier too high (> 11.0)")

    if modifier == 1.0:
        modifier = None

    return modifier


def _clean_source_slug(source_slug, sources_by_slug, errors):
    source = sources_by_slug.get(source_slug)
    if source is None:
        errors.append("Invalid Source Slug")

    return source


def _clean_publisher(publisher, errors):
    publisher = publisher.strip()
    prefixes = ("http://", "https://")
    if any(publisher.startswith(x) for x in prefixes):
        errors.append("Remove the following prefixes: http, https")

    for prefix in ("http://", "https://"):
        publisher = publisher.replace(prefix, "")

    if "/" in publisher:
        errors.append("Publisher should not contain /")
        publisher = publisher.strip("/")

    return publisher
