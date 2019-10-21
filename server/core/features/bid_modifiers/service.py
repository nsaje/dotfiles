import csv
import dataclasses
import io as StringIO
import os
from collections import defaultdict
from typing import Sequence

from django.conf import settings
from django.db import transaction

from core.models.source import model as source_model
from dash import constants as dash_constants
from utils import k1_helper
from utils import s3helpers

from . import constants
from . import exceptions
from . import helpers
from . import models

set_built_in = set


@dataclasses.dataclass
class BidModifierData:
    type: int
    target: str
    source: source_model.Source
    modifier: float


def get(ad_group, include_types=None, exclude_types=None):
    qs = models.BidModifier.objects.filter(ad_group=ad_group).select_related("source").order_by("pk")

    if include_types:
        qs = qs.filter(type__in=include_types)
    if exclude_types:
        qs = qs.exclude(type__in=exclude_types)

    return [{"type": item.type, "target": item.target, "source": item.source, "modifier": item.modifier} for item in qs]


@transaction.atomic
def set(ad_group, modifier_type, target, source, modifier, user=None, write_history=True, propagate_to_k1=True):
    instance, created = _set(ad_group, modifier_type, target, source, modifier, user, write_history)
    if propagate_to_k1:
        k1_helper.update_ad_group(ad_group, msg="bid_modifiers.set", priority=True)
    return instance, created


@transaction.atomic
def set_bulk(
    ad_group, bid_modifiers_to_set: Sequence[BidModifierData], user=None, write_history=True, propagate_to_k1=True
):
    instances = []
    for bid_modifier_data in bid_modifiers_to_set:
        instance, _ = _set(
            ad_group,
            bid_modifier_data.type,
            bid_modifier_data.target,
            bid_modifier_data.source,
            bid_modifier_data.modifier,
            user,
        )
        if instance:
            instances.append(instance)
    if propagate_to_k1:
        k1_helper.update_ad_group(ad_group, msg="bid_modifiers.set", priority=True)
    return instances


def _set(ad_group, modifier_type, target, source, modifier, user, write_history=True):
    if not modifier:
        _delete(ad_group, modifier_type, target, source, user=user, write_history=write_history)
        return None, None

    if modifier_type != constants.BidModifierType.SOURCE:
        helpers.check_modifier_value(modifier)

    return _update_or_create(ad_group, modifier_type, target, source, modifier, user=user, write_history=write_history)


def _delete(ad_group, modifier_type, target, source, user=None, write_history=True):
    source_slug = helpers.get_source_slug(modifier_type, source)

    num_deleted, deleted = models.BidModifier.objects.filter(
        type=modifier_type, ad_group=ad_group, source_slug=source_slug, target=target
    ).delete()

    if write_history and num_deleted > 0:
        ad_group.write_history(
            "Reset bid modifier: %s" % helpers.describe_bid_modifier(modifier_type, target, source),
            user=user,
            action_type=dash_constants.HistoryActionType.BID_MODIFIER_DELETE,
        )
    return num_deleted, deleted


def _update_or_create(ad_group, modifier_type, target, source, modifier, user=None, write_history=True):
    source_slug = helpers.get_source_slug(modifier_type, source)

    instance, created = models.BidModifier.objects.update_or_create(
        defaults={"modifier": modifier, "source": source},
        type=modifier_type,
        ad_group=ad_group,
        source_slug=source_slug,
        target=target,
    )

    if write_history:
        percentage = "{:.2%}".format(modifier - 1.0)
        ad_group.write_history(
            "Bid modifier %s set to %s." % (helpers.describe_bid_modifier(modifier_type, target, source), percentage),
            user=user,
            action_type=dash_constants.HistoryActionType.BID_MODIFIER_UPDATE,
        )

    return instance, created


@transaction.atomic
def delete(ad_group, input_bid_modifier_ids, user=None, write_history=True):
    bid_modifiers_qs = models.BidModifier.objects.filter(ad_group_id=ad_group.id)
    if user:
        bid_modifiers_qs = bid_modifiers_qs.filter_by_user(user)
    bid_modifiers_qs = bid_modifiers_qs.filter(id__in=input_bid_modifier_ids)

    bid_modifier_ids = bid_modifiers_qs.values_list("id", flat=True)
    if set_built_in(bid_modifier_ids).symmetric_difference(set_built_in(input_bid_modifier_ids)):
        raise exceptions.BidModifierDeleteInvalidIds("Invalid Bid Modifier ids")

    num_deleted, _ = bid_modifiers_qs.delete()
    if write_history:
        ad_group.write_history(
            "Removed %s bid modifier%s." % (num_deleted, "s" if num_deleted > 1 else ""),
            user=user,
            action_type=dash_constants.HistoryActionType.BID_MODIFIER_DELETE,
        )


@transaction.atomic
def set_from_cleaned_entries(ad_group, cleaned_entries, user=None, write_history=True, propagate_to_k1=True):
    for entry in cleaned_entries:
        set(
            ad_group,
            entry["type"],
            entry["target"],
            entry["source"],
            entry["modifier"],
            user=user,
            write_history=write_history,
            propagate_to_k1=False,
        )

    if propagate_to_k1:
        k1_helper.update_ad_group(ad_group, msg="bid_modifiers.set_from_cleaned_entries")


def clean_entries(entries):
    cleaned_entries = []
    has_error = False
    sources_by_slug = {x.get_clean_slug(): x for x in source_model.Source.objects.all()}

    for entry in entries:
        errors = []

        modifier_type, target_column_name = helpers.extract_modifier_type(entry.keys())
        modifier = helpers.clean_bid_modifier_value_input(entry["Bid Modifier"], errors)
        if modifier_type is None:
            entry["Errors"] = "; ".join(errors)
            has_error = True
            continue

        if modifier_type == constants.BidModifierType.PUBLISHER:
            source = helpers.clean_source_bidder_slug_input(entry["Source Slug"], sources_by_slug, errors)
            if entry[target_column_name] == "all publishers":
                # We don't add 'all publishers' row to cleaned entries.
                if modifier is not None:
                    errors.append("'all publishers' can not have a bid modifier set")
                    entry["Errors"] = "; ".join(errors)
                    has_error = True

                continue
        else:
            source = None

        target = helpers.clean_target_input(entry[target_column_name], modifier_type, errors)

        if not errors:
            cleaned_entries.append({"type": modifier_type, "modifier": modifier, "target": target, "source": source})
        else:
            entry["Errors"] = "; ".join(errors)
            has_error = True

    return cleaned_entries, has_error


def parse_csv_file_entries(csv_file, modifier_type=None):
    csv_reader = csv.DictReader(csv_file)

    if csv_reader.fieldnames is None:
        raise exceptions.InvalidBidModifierFile("The file is not a proper CSV file!")

    detected_modifier_type, target_column_name = helpers.extract_modifier_type(csv_reader.fieldnames)

    if modifier_type:
        if modifier_type != detected_modifier_type:
            raise exceptions.InvalidBidModifierFile("Input file does not match requested Bid Modifier type")
    else:
        modifier_type = detected_modifier_type

    if modifier_type == constants.BidModifierType.PUBLISHER and "Source Slug" not in csv_reader.fieldnames:
        raise exceptions.InvalidBidModifierFile("Source Slug column missing in CSV file")
    elif modifier_type != constants.BidModifierType.PUBLISHER and "Source Slug" in csv_reader.fieldnames:
        raise exceptions.InvalidBidModifierFile("Source Slug should exist only in publisher bid modifier CSV file")

    if "Bid Modifier" not in csv_reader.fieldnames:
        raise exceptions.InvalidBidModifierFile("Bid Modifier column missing in CSV file")

    entries = []

    for row in csv_reader:
        entry = {target_column_name: row[target_column_name], "Bid Modifier": row["Bid Modifier"]}
        if modifier_type == constants.BidModifierType.PUBLISHER:
            entry.update({"Source Slug": row["Source Slug"]})

        entries.append(entry)

    return entries


def process_csv_file_upload(ad_group, csv_file, modifier_type=None, user=None):
    entries = parse_csv_file_entries(csv_file, modifier_type=modifier_type)
    cleaned_entries, error = clean_entries(entries)

    if error:
        modifier_type, target_column_name = helpers.extract_modifier_type(entries[0])
        error_csv_columns = helpers.make_csv_file_columns(modifier_type) + ["Errors"]
        return make_and_store_csv_error_file(entries, error_csv_columns, ad_group.id)

    set_from_cleaned_entries(ad_group, cleaned_entries, user=user)
    return None


def process_bulk_csv_file_upload(ad_group, bulk_csv_file, user=None):
    sub_files = helpers.split_bulk_csv_file(bulk_csv_file)
    entries_list = []

    for sub_file in sub_files:
        try:
            entries_list.append(parse_csv_file_entries(sub_file))
        except exceptions.InvalidBidModifierFile as e:
            entries_list.append(e)

    overall_error = False
    cleaned_entries_list = []

    for entries in entries_list:
        if isinstance(entries, exceptions.InvalidBidModifierFile):
            overall_error = True
        else:
            cleaned_entries, error = clean_entries(entries)

            if error:
                overall_error = True

            cleaned_entries_list.append(cleaned_entries)

    if not overall_error:
        set_from_cleaned_entries(
            ad_group,
            [
                e
                for cleaned_entries in cleaned_entries_list
                for e in cleaned_entries
                # TEMP(tkusterle) temporarily disable source bid modifiers
                if e["type"] != constants.BidModifierType.SOURCE
            ],
            user=user,
        )
        return None

    def sub_file_generator(entries_list, sub_files):
        for idx, entries in enumerate(entries_list):
            if isinstance(entries, exceptions.InvalidBidModifierFile):
                sub_file = sub_files[idx]
                sub_file.seek(0)
                message_buffer = StringIO.StringIO()
                message_buffer.write(str(entries) + csv.excel.lineterminator)
                message_buffer.write(sub_file.read())
                message_buffer.seek(0)
                yield message_buffer
            else:
                modifier_type, target_column_name = helpers.extract_modifier_type(entries[0])
                error_csv_columns = helpers.make_csv_file_columns(modifier_type) + ["Errors"]
                yield make_csv_error_file(entries, error_csv_columns)

    csv_error_key = helpers.create_csv_error_key()

    csv_error_content = helpers.create_bulk_csv_file(sub_file_generator(entries_list, sub_files))

    s3_helper = s3helpers.S3Helper(settings.S3_BUCKET_PUBLISHER_GROUPS)
    s3_helper.put(
        os.path.join("bid_modifier_errors", "ad_group_{}".format(ad_group.id), csv_error_key + ".csv"),
        csv_error_content,
    )
    return csv_error_key


def make_csv_file(modifier_type, cleaned_entries):
    target_column_name = helpers.output_modifier_type(modifier_type)
    csv_columns = helpers.make_csv_file_columns(modifier_type)

    def rows(entries):
        for entry in entries:
            row = {
                target_column_name: helpers.transform_target(modifier_type, entry["target"]),
                "Bid Modifier": str(entry["modifier"]),
            }

            if modifier_type == constants.BidModifierType.PUBLISHER:
                row.update({"Source Slug": helpers.output_source_bidder_slug(entry["source"])})

            yield row

    csv_file = StringIO.StringIO()
    writer = csv.DictWriter(csv_file, csv_columns, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows(cleaned_entries))
    csv_file.seek(0)
    return csv_file


def make_bulk_csv_file(cleaned_entries):
    cleaned_entries.sort(key=lambda x: x["type"])
    type_dict = defaultdict(list)
    for entry in cleaned_entries:
        type_dict[entry["type"]].append(entry)

    def sub_file_generator(type_dict):
        for modifier_type, entries in type_dict.items():
            yield make_csv_file(modifier_type, entries)

    return helpers.create_bulk_csv_file(sub_file_generator(type_dict))


def make_and_store_csv_error_file(entries, csv_columns, ad_group_id):
    csv_error_file = StringIO.StringIO()
    csv_error_writer = csv.DictWriter(csv_error_file, csv_columns, extrasaction="ignore")
    csv_error_writer.writeheader()
    csv_error_writer.writerows(entries)

    csv_error_content = csv_error_file.getvalue()
    csv_error_key = helpers.create_csv_error_key()

    s3_helper = s3helpers.S3Helper(settings.S3_BUCKET_PUBLISHER_GROUPS)
    s3_helper.put(
        os.path.join("bid_modifier_errors", "ad_group_{}".format(ad_group_id), csv_error_key + ".csv"),
        csv_error_content,
    )

    return csv_error_key


def make_csv_error_file(entries, csv_columns):
    csv_error_file = StringIO.StringIO()
    csv_error_writer = csv.DictWriter(csv_error_file, csv_columns, extrasaction="ignore")
    csv_error_writer.writeheader()
    csv_error_writer.writerows(entries)
    csv_error_file.seek(0)

    return csv_error_file


def make_csv_example_file(modifier_type):
    target_column_name = helpers.output_modifier_type(modifier_type)
    csv_columns = helpers.make_csv_file_columns(modifier_type)

    entry = {"Bid Modifier": "1.0"}

    modifier_type_map = {
        constants.BidModifierType.PUBLISHER: {target_column_name: "example.com", "Source Slug": "some_slug"},
        constants.BidModifierType.SOURCE: {target_column_name: "b1_outbrain"},
        constants.BidModifierType.DEVICE: {
            target_column_name: dash_constants.DeviceType.get_name(dash_constants.DeviceType.MOBILE)
        },
        constants.BidModifierType.OPERATING_SYSTEM: {
            target_column_name: dash_constants.OperatingSystem.get_text(dash_constants.OperatingSystem.ANDROID)
        },
        constants.BidModifierType.PLACEMENT: {
            target_column_name: dash_constants.PlacementMedium.get_name(dash_constants.PlacementMedium.SITE)
        },
        constants.BidModifierType.COUNTRY: {target_column_name: "US"},
        constants.BidModifierType.STATE: {target_column_name: "US-TX"},
        constants.BidModifierType.DMA: {target_column_name: "765"},
        constants.BidModifierType.AD: {target_column_name: "1"},
        constants.BidModifierType.DAY_HOUR: {target_column_name: "MONDAY_12"},
    }

    entry.update(modifier_type_map[modifier_type])

    csv_example_file = StringIO.StringIO()
    writer = csv.DictWriter(csv_example_file, csv_columns, extrasaction="ignore")
    writer.writeheader()
    writer.writerows([entry])
    csv_example_file.seek(0)
    return csv_example_file


def make_bulk_csv_example_file():
    def sub_file_generator():
        for modifier_type in constants.BidModifierType.get_all():
            # TEMP(tkusterle) temporarily disable source bid modifiers
            if modifier_type == constants.BidModifierType.SOURCE:
                continue

            yield make_csv_example_file(modifier_type)

    return helpers.create_bulk_csv_file(sub_file_generator())
