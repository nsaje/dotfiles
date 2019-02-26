import csv
import io as StringIO
import numbers
import os
import random
import string

from django.conf import settings
from django.db import transaction

from core.models.source import model as source_model
from dash import constants as dash_constants
from utils import s3helpers

from . import constants
from . import exceptions
from . import helpers
from . import models


def get(ad_group, include_types=None, exclude_types=None):
    qs = models.BidModifier.objects.filter(ad_group=ad_group).select_related("source").order_by("pk")

    if include_types:
        qs = qs.filter(type__in=include_types)
    if exclude_types:
        qs = qs.exclude(type__in=exclude_types)

    return [{"type": item.type, "target": item.target, "source": item.source, "modifier": item.modifier} for item in qs]


@transaction.atomic
def set(ad_group, modifier_type, target, source, modifier, user=None, write_history=True):
    if not modifier:
        num_deleted, result = _delete(ad_group, modifier_type, target, source)
        if write_history and num_deleted > 0:
            ad_group.write_history(
                "Reset bid modifier: %s" % helpers.describe_bid_modifier(modifier_type, target, source), user=user
            )
        return

    if not isinstance(modifier, numbers.Number) or not helpers.modifier_bounds_ok(modifier):
        raise exceptions.BidModifierValueInvalid

    _update_or_create(ad_group, modifier_type, target, source, modifier)
    if write_history:
        percentage = "{:.2%}".format(modifier - 1.0)
        ad_group.write_history(
            "Bid modifier %s set to %s." % (helpers.describe_bid_modifier(modifier_type, target, source), percentage),
            user=user,
        )


def _delete(ad_group, modifier_type, target, source):
    source_slug = helpers.get_source_slug(modifier_type, source)
    return models.BidModifier.objects.filter(
        type=modifier_type, ad_group=ad_group, source_slug=source_slug, target=target
    ).delete()


def _update_or_create(ad_group, modifier_type, target, source, modifier):
    source_slug = helpers.get_source_slug(modifier_type, source)
    return models.BidModifier.objects.update_or_create(
        defaults={"modifier": modifier, "source": source},
        type=modifier_type,
        ad_group=ad_group,
        source_slug=source_slug,
        target=target,
    )


def set_from_cleaned_entries(ad_group, cleaned_entries, user=None, write_history=True):
    for entry in cleaned_entries:
        set(
            ad_group,
            entry["type"],
            entry["target"],
            entry["source"],
            entry["modifier"],
            user=user,
            write_history=write_history,
        )


def clean_entries(entries):
    cleaned_entries = []
    has_error = False
    sources_by_slug = {x.get_clean_slug(): x for x in source_model.Source.objects.all()}

    for entry in entries:
        errors = []

        modifier_type = helpers.clean_bid_modifier_type_input(entry["Type"], errors)
        modifier = helpers.clean_bid_modifier_value_input(entry["Bid Modifier"], errors)
        if modifier_type is None:
            entry["Errors"] = "; ".join(errors)
            has_error = True
            continue

        if modifier_type == constants.BidModifierType.PUBLISHER:
            source = helpers.clean_source_bidder_slug_input(entry["Source Slug"], sources_by_slug, errors)
            target = helpers.clean_publisher_input(entry["Target"], errors)
        else:
            source = None
            if entry["Source Slug"]:
                errors.append("Source Slug must be empty for non-publisher bid modifier")

            if modifier_type == constants.BidModifierType.SOURCE:
                target = helpers.clean_source_input(entry["Target"], errors)
            elif modifier_type == constants.BidModifierType.DEVICE:
                target = helpers.clean_device_type_input(entry["Target"], errors)
            elif modifier_type == constants.BidModifierType.OPERATING_SYSTEM:
                target = helpers.clean_operating_system_input(entry["Target"], errors)
            elif modifier_type == constants.BidModifierType.PLACEMENT:
                target = helpers.clean_placement_medium_input(entry["Target"], errors)
            else:
                target = helpers.clean_geolocation_input(entry["Target"], modifier_type, errors)

        # We don't add 'all publishers' row to cleaned entries.
        if modifier_type == constants.BidModifierType.PUBLISHER and entry["Target"] == "all publishers":
            if entry["Bid Modifier"] != "":
                errors.append("'all publishers' can not have a bid modifier set")
        elif not errors:
            cleaned_entries.append({"type": modifier_type, "modifier": modifier, "target": target, "source": source})

        if errors:
            entry["Errors"] = "; ".join(errors)
            has_error = True

    return cleaned_entries, has_error


def parse_csv_file_entries(csv_file):
    csv_reader = csv.DictReader(csv_file)

    if csv_reader.fieldnames is None:
        raise exceptions.InvalidBidModifierFile("The file is not a proper CSV file!")

    if "Type" not in csv_reader.fieldnames:
        raise exceptions.InvalidBidModifierFile("Type column missing in CSV file!")

    if "Target" not in csv_reader.fieldnames:
        raise exceptions.InvalidBidModifierFile("Target column missing in CSV file!")

    if "Source Slug" not in csv_reader.fieldnames:
        raise exceptions.InvalidBidModifierFile("Source Slug column missing in CSV file!")

    if "Bid Modifier" not in csv_reader.fieldnames:
        raise exceptions.InvalidBidModifierFile("Bid Modifier column missing in CSV file!")

    return list(csv_reader)


def make_csv_file(cleaned_entries):
    csv_columns = ["Type", "Target", "Source Slug", "Bid Modifier"]

    def rows(entries):
        transformation_map = {
            constants.BidModifierType.PUBLISHER: lambda x: x,
            constants.BidModifierType.SOURCE: helpers.output_source_target,
            constants.BidModifierType.DEVICE: helpers.output_device_type_target,
            constants.BidModifierType.OPERATING_SYSTEM: helpers.output_operating_system_target,
            constants.BidModifierType.PLACEMENT: helpers.output_placement_medium_target,
            constants.BidModifierType.COUNTRY: lambda x: x,
            constants.BidModifierType.STATE: lambda x: x,
            constants.BidModifierType.DMA: lambda x: x,
        }

        for entry in entries:
            yield {
                "Type": helpers.output_modifier_type(entry["type"]),
                "Target": transformation_map[entry["type"]](entry["target"]),
                "Source Slug": helpers.output_source_bidder_slug(entry["source"]),
                "Bid Modifier": str(entry["modifier"]),
            }

    csv_file = StringIO.StringIO()
    writer = csv.DictWriter(csv_file, csv_columns, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows(cleaned_entries))
    csv_file.seek(0)
    return csv_file


def make_csv_error_file(entries, csv_columns, ad_group_id):
    csv_error_file = StringIO.StringIO()
    csv_error_writer = csv.DictWriter(csv_error_file, csv_columns, extrasaction="ignore")
    csv_error_writer.writeheader()
    csv_error_writer.writerows(entries)

    csv_error_content = csv_error_file.getvalue()
    csv_error_key = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(64))

    s3_helper = s3helpers.S3Helper(settings.S3_BUCKET_PUBLISHER_GROUPS)
    s3_helper.put(
        os.path.join("bid_modifier_errors", "ad_group_{}".format(ad_group_id), csv_error_key + ".csv"),
        csv_error_content,
    )

    return csv_error_key


def make_csv_example_file():
    csv_columns = ["Type", "Target", "Source Slug", "Bid Modifier"]
    entries = [
        {
            "Type": helpers.output_modifier_type(constants.BidModifierType.PUBLISHER),
            "Target": "example.com",
            "Source Slug": "some_slug",
            "Bid Modifier": "1.1",
        },
        {
            "Type": helpers.output_modifier_type(constants.BidModifierType.SOURCE),
            "Target": "b1_outbrain",
            "Source Slug": "",
            "Bid Modifier": "1.2",
        },
        {
            "Type": helpers.output_modifier_type(constants.BidModifierType.DEVICE),
            "Target": dash_constants.DeviceType.get_text(dash_constants.DeviceType.MOBILE),
            "Source Slug": "",
            "Bid Modifier": "1.3",
        },
        {
            "Type": helpers.output_modifier_type(constants.BidModifierType.OPERATING_SYSTEM),
            "Target": dash_constants.OperatingSystem.get_text(dash_constants.OperatingSystem.ANDROID),
            "Source Slug": "",
            "Bid Modifier": "1.4",
        },
        {
            "Type": helpers.output_modifier_type(constants.BidModifierType.PLACEMENT),
            "Target": dash_constants.PlacementMedium.get_text(dash_constants.PlacementMedium.SITE),
            "Source Slug": "",
            "Bid Modifier": "1.5",
        },
        {
            "Type": helpers.output_modifier_type(constants.BidModifierType.COUNTRY),
            "Target": "US",
            "Source Slug": "",
            "Bid Modifier": "1.6",
        },
        {
            "Type": helpers.output_modifier_type(constants.BidModifierType.STATE),
            "Target": "US-TX",
            "Source Slug": "",
            "Bid Modifier": "1.7",
        },
        {
            "Type": helpers.output_modifier_type(constants.BidModifierType.DMA),
            "Target": "765",
            "Source Slug": "",
            "Bid Modifier": "1.8",
        },
    ]

    csv_example_file = StringIO.StringIO()
    writer = csv.DictWriter(csv_example_file, csv_columns, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(entries)
    csv_example_file.seek(0)
    return csv_example_file
