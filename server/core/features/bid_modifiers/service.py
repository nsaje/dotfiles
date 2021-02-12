import csv
import dataclasses
import io as StringIO
from collections import defaultdict
from decimal import Decimal
from typing import Sequence

from django.conf import settings
from django.db import transaction
from django.db.models import Count

import core.models
from core.models.source import model as source_model
from dash import constants as dash_constants
from utils import decimal_helpers
from utils import k1_helper
from utils import s3helpers
from zemauth.features.entity_permission import Permission

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
def set(
    ad_group,
    modifier_type,
    target,
    source,
    modifier,
    user=None,
    write_history=True,
    propagate_to_k1=True,
    skip_source_settings_update=False,
    skip_validation=False,
):
    if not _is_unset(modifier_type, modifier):
        core.common.entity_limits.enforce(
            models.BidModifier.objects.filter(ad_group=ad_group), ad_group.campaign.account_id
        )

    if modifier_type == constants.BidModifierType.AD:
        if not core.models.ContentAd.objects.filter(ad_group=ad_group, id=target).exists():
            raise exceptions.BidModifierTargetAdGroupMismatch("Target content ad is not a part of this ad group")

    instance, created = _set(
        ad_group,
        modifier_type,
        target,
        source,
        modifier,
        user,
        write_history,
        skip_source_settings_update=skip_source_settings_update,
        skip_validation=skip_validation,
    )
    if propagate_to_k1:
        k1_helper.update_ad_group(ad_group, msg="bid_modifiers.set", priority=True)
    return instance, created


@transaction.atomic
def set_bulk(
    ad_group,
    bid_modifiers_to_set: Sequence[BidModifierData],
    user=None,
    write_history=True,
    propagate_to_k1=True,
    skip_validation=False,
):
    to_delete_count = sum(1 for bm in bid_modifiers_to_set if _is_unset(bm.type, bm.modifier))
    core.common.entity_limits.enforce(
        models.BidModifier.objects.filter(ad_group=ad_group),
        ad_group.campaign.account_id,
        create_count=len(bid_modifiers_to_set) - 2 * to_delete_count,
    )

    target_ad_ids = {bm.target for bm in bid_modifiers_to_set if bm.type == constants.BidModifierType.AD}
    if target_ad_ids:
        if core.models.ContentAd.objects.filter(ad_group=ad_group, id__in=target_ad_ids).count() != len(target_ad_ids):
            raise exceptions.BidModifierTargetAdGroupMismatch(
                "At least one of the target content ads is not a part of this ad group"
            )

    instances = []
    for bid_modifier_data in bid_modifiers_to_set:
        instance, _ = _set(
            ad_group,
            bid_modifier_data.type,
            bid_modifier_data.target,
            bid_modifier_data.source,
            bid_modifier_data.modifier,
            user,
            write_history=write_history,
            skip_validation=skip_validation,
        )
        if instance:
            instances.append(instance)
    if propagate_to_k1:
        k1_helper.update_ad_group(ad_group, msg="bid_modifiers.set", priority=True)
    return instances


def _set(
    ad_group,
    modifier_type,
    target,
    source,
    modifier,
    user,
    write_history=True,
    skip_source_settings_update=False,
    skip_validation=False,
):
    if _is_unset(modifier_type, modifier):
        _delete(ad_group, modifier_type, target, source, user=user, write_history=write_history)
        if modifier_type == constants.BidModifierType.SOURCE and not skip_source_settings_update:
            _update_ad_group_source_settings(ad_group, target, modifier, user, skip_validation=skip_validation)
        return None, None

    if modifier_type != constants.BidModifierType.SOURCE:
        helpers.check_modifier_value(modifier)

    instance, created = _update_or_create(
        ad_group, modifier_type, target, source, modifier, user=user, write_history=write_history
    )

    if modifier_type == constants.BidModifierType.SOURCE and not skip_source_settings_update:
        _update_ad_group_source_settings(ad_group, target, modifier, user, skip_validation=skip_validation)

    return instance, created


def _is_unset(modifier_type, modifier):
    # TODO publisher modifiers with value of 1 are currently needed to correctly support publisher hierarchy in bidder
    return (modifier == 1.0 and modifier_type != constants.BidModifierType.PUBLISHER) or not modifier


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

    instance, created = models.BidModifier.objects.get_or_create(
        defaults={"modifier": modifier, "source": source},
        type=modifier_type,
        ad_group=ad_group,
        source_slug=source_slug,
        target=target,
    )

    change = created
    if not change:
        change = not decimal_helpers.equal_decimals(modifier, instance.modifier, precision=Decimal("1.00000000"))
        if change:
            instance.modifier = modifier
            instance.save()

    if write_history and change:
        percentage = "{:.2%}".format(modifier - 1.0)
        ad_group.write_history(
            "Bid modifier %s set to %s." % (helpers.describe_bid_modifier(modifier_type, target, source), percentage),
            user=user,
            action_type=dash_constants.HistoryActionType.BID_MODIFIER_UPDATE,
        )

    return instance, created


def _update_ad_group_source_settings(
    ad_group, target, modifier, user, write_history=True, propagate_to_k1=False, skip_validation=False
):
    agency_uses_realtime_autopilot = ad_group.campaign.account.agency_uses_realtime_autopilot()
    autopilot_active = ad_group.settings.autopilot_state != dash_constants.AdGroupSettingsAutopilotState.INACTIVE

    if agency_uses_realtime_autopilot and autopilot_active:
        return

    try:
        ad_group_source = ad_group.adgroupsource_set.select_related("settings").get(source__id=int(target))
    except core.models.AdGroupSource.DoesNotExist:
        return

    updates = {}
    if ad_group.bidding_type == dash_constants.BiddingType.CPC:
        updates["cpc_cc"] = decimal_helpers.multiply_as_decimals(ad_group.settings.cpc, modifier)
    else:
        updates["cpm"] = decimal_helpers.multiply_as_decimals(ad_group.settings.cpm, modifier)

    ad_group_source.settings.update(
        k1_sync=propagate_to_k1, write_history=write_history, skip_validation=skip_validation, **updates
    )


@transaction.atomic
def delete(ad_group, input_bid_modifier_ids, user=None, write_history=True, propagate_to_k1=True):
    bid_modifiers_qs = models.BidModifier.objects.filter(ad_group_id=ad_group.id)
    if user:
        bid_modifiers_qs = _filter_bid_modifiers_by_user_access(bid_modifiers_qs, user, Permission.WRITE)
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

    if propagate_to_k1 and num_deleted > 0:
        k1_helper.update_ad_group(ad_group, msg="bid_modifiers.delete", priority=True)


@transaction.atomic
def delete_types(ad_group, types_list, user=None, write_history=True, propagate_to_k1=True):
    if not types_list:
        return

    bid_modifiers_qs = models.BidModifier.objects.filter(ad_group_id=ad_group.id, type__in=types_list)
    if user:
        bid_modifiers_qs = _filter_bid_modifiers_by_user_access(bid_modifiers_qs, user, Permission.WRITE)

    num_deleted, _ = bid_modifiers_qs.delete()
    if write_history:
        ad_group.write_history(
            "Removed %s bid modifier%s." % (num_deleted, "s" if num_deleted > 1 else ""),
            user=user,
            action_type=dash_constants.HistoryActionType.BID_MODIFIER_DELETE,
        )

    if propagate_to_k1 and num_deleted > 0:
        k1_helper.update_ad_group(ad_group, msg="bid_modifiers.delete", priority=True)

    return num_deleted


def count_types(ad_group_id, types_list, user=None):
    if not types_list:
        return

    bid_modifiers_qs = models.BidModifier.objects.filter(ad_group_id=ad_group_id, type__in=types_list)
    if user:
        bid_modifiers_qs = _filter_bid_modifiers_by_user_access(bid_modifiers_qs, user, Permission.READ)

    return bid_modifiers_qs.values("type").annotate(count=Count("type"))


@transaction.atomic
def set_from_cleaned_entries(ad_group, cleaned_entries, user=None, write_history=True, propagate_to_k1=True):
    instances = []
    for entry in cleaned_entries:
        instance, _ = set(
            ad_group,
            entry["type"],
            entry["target"],
            entry["source"],
            entry["modifier"],
            user=user,
            write_history=write_history,
            propagate_to_k1=False,
        )
        instances.append(instance)

    if propagate_to_k1:
        k1_helper.update_ad_group(ad_group, msg="bid_modifiers.set_from_cleaned_entries")

    return instances


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

        if modifier_type in (constants.BidModifierType.PUBLISHER, constants.BidModifierType.PLACEMENT):
            source = helpers.clean_source_bidder_slug_input(entry["Source Slug"], sources_by_slug, errors)
            if modifier_type == constants.BidModifierType.PUBLISHER and entry[target_column_name] == "all publishers":
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

    if (
        modifier_type in (constants.BidModifierType.PUBLISHER, constants.BidModifierType.PLACEMENT)
        and "Source Slug" not in csv_reader.fieldnames
    ):
        raise exceptions.InvalidBidModifierFile("Source Slug column missing in CSV file")
    elif (
        modifier_type not in (constants.BidModifierType.PUBLISHER, constants.BidModifierType.PLACEMENT)
        and "Source Slug" in csv_reader.fieldnames
    ):
        raise exceptions.InvalidBidModifierFile(
            "Source Slug should exist only in publisher or placement bid modifier CSV file"
        )

    if "Bid Modifier" not in csv_reader.fieldnames:
        raise exceptions.InvalidBidModifierFile("Bid Modifier column missing in CSV file")

    entries = []

    for row in csv_reader:
        entry = {target_column_name: row[target_column_name], "Bid Modifier": row["Bid Modifier"]}
        if modifier_type in (constants.BidModifierType.PUBLISHER, constants.BidModifierType.PLACEMENT):
            entry.update({"Source Slug": row["Source Slug"]})

        entries.append(entry)

    return entries, modifier_type


def validate_csv_file_upload(ad_group_id, csv_file, modifier_type=None):
    entries, modifier_type = parse_csv_file_entries(csv_file, modifier_type=modifier_type)
    cleaned_entries, error = clean_entries(entries)

    if error:
        modifier_type, target_column_name = helpers.extract_modifier_type(entries[0])
        error_csv_columns = helpers.make_csv_file_columns(modifier_type) + ["Errors"]
        return [], modifier_type, make_and_store_csv_error_file(entries, error_csv_columns, ad_group_id)

    return cleaned_entries, modifier_type, None


def process_csv_file_upload(ad_group, csv_file, modifier_type=None, user=None):
    cleaned_entries, modifier_type, csv_error_key = validate_csv_file_upload(
        ad_group, csv_file, modifier_type=modifier_type
    )

    if csv_error_key is not None:
        return 0, [], csv_error_key

    with transaction.atomic():
        number_of_deleted = delete_types(
            ad_group, [modifier_type], user=user, write_history=False, propagate_to_k1=False
        )
        created_instances = set_from_cleaned_entries(
            ad_group, cleaned_entries, user=user, write_history=False, propagate_to_k1=False
        )
        _write_upload_history(ad_group, number_of_deleted, len(created_instances), user=user)
        k1_helper.update_ad_group(ad_group, msg="bid_modifiers.set", priority=True)

    return number_of_deleted, created_instances, None


def validate_bulk_csv_file_upload(ad_group_id, bulk_csv_file):
    sub_files = helpers.split_bulk_csv_file(bulk_csv_file)
    entries_list = []

    for sub_file in sub_files:
        try:
            entries_list.append(parse_csv_file_entries(sub_file)[0])
        except exceptions.InvalidBidModifierFile as e:
            entries_list.append(e)

    overall_error = False
    cleaned_entries = []

    for entries in entries_list:
        if isinstance(entries, exceptions.InvalidBidModifierFile):
            overall_error = True
        else:
            cleaned_entries_for_type, error = clean_entries(entries)

            if error:
                overall_error = True

            cleaned_entries.extend(cleaned_entries_for_type)

    if not overall_error:
        return cleaned_entries, None

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

    csv_error_content = helpers.create_bulk_csv_file(sub_file_generator(entries_list, sub_files)).getvalue()

    s3_helper = s3helpers.S3Helper(settings.S3_BUCKET_PUBLISHER_GROUPS)
    s3_helper.put(helpers.create_error_file_path(ad_group_id, csv_error_key), csv_error_content)
    return [], csv_error_key


def process_bulk_csv_file_upload(ad_group, bulk_csv_file, user=None):
    cleaned_entries, csv_error_key = validate_bulk_csv_file_upload(ad_group, bulk_csv_file)

    if csv_error_key:
        return 0, [], csv_error_key

    with transaction.atomic():
        number_of_deleted = delete_types(
            ad_group, constants.BidModifierType.get_all(), user=user, write_history=False, propagate_to_k1=False
        )
        created_instances = set_from_cleaned_entries(
            ad_group, cleaned_entries, user=user, write_history=False, propagate_to_k1=False
        )
        _write_upload_history(ad_group, number_of_deleted, len(created_instances), user=user)
        k1_helper.update_ad_group(ad_group, msg="bid_modifiers.set", priority=True)

    return number_of_deleted, created_instances, None


def make_csv_file(modifier_type, cleaned_entries):
    target_column_name = helpers.output_modifier_type(modifier_type)
    csv_columns = helpers.make_csv_file_columns(modifier_type)

    def rows(entries):
        for entry in entries:
            row = {
                target_column_name: helpers.transform_target(modifier_type, entry["target"]),
                "Bid Modifier": str(entry["modifier"]),
            }

            if modifier_type in (constants.BidModifierType.PUBLISHER, constants.BidModifierType.PLACEMENT):
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
    s3_helper.put(helpers.create_error_file_path(ad_group_id, csv_error_key), csv_error_content)

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

    modifier_type_map = {
        constants.BidModifierType.PUBLISHER: [{target_column_name: "example.com", "Source Slug": "some_slug"}],
        constants.BidModifierType.PLACEMENT: [
            {target_column_name: "example.com__1__someplacement", "Source Slug": "some_slug"}
        ],
        constants.BidModifierType.SOURCE: [{target_column_name: "b1_outbrain"}],
        constants.BidModifierType.DEVICE: _get_constant_examples(
            target_column_name,
            dash_constants.DeviceType,
            [dash_constants.DeviceType.UNKNOWN, dash_constants.DeviceType.TV],
        ),
        constants.BidModifierType.OPERATING_SYSTEM: _get_constant_examples(
            target_column_name, dash_constants.OperatingSystem, [dash_constants.OperatingSystem.UNKNOWN]
        ),
        constants.BidModifierType.ENVIRONMENT: _get_constant_examples(
            target_column_name, dash_constants.Environment, [dash_constants.Environment.UNKNOWN]
        ),
        constants.BidModifierType.COUNTRY: [{target_column_name: "US"}],
        constants.BidModifierType.STATE: [{target_column_name: "US-TX"}],
        constants.BidModifierType.DMA: [{target_column_name: "765"}],
        constants.BidModifierType.AD: [{target_column_name: "1"}],
        constants.BidModifierType.DAY_HOUR: [{target_column_name: "MONDAY_0"}, {target_column_name: "SUNDAY_23"}],
        constants.BidModifierType.BROWSER: _get_constant_examples(
            target_column_name,
            dash_constants.BrowserFamily,
            [dash_constants.BrowserFamily.UNKNOWN, dash_constants.BrowserFamily.IN_APP],
        ),
        constants.BidModifierType.CONNECTION_TYPE: _get_constant_examples(
            target_column_name, dash_constants.ConnectionType, [dash_constants.ConnectionType.UNKNOWN]
        ),
    }

    entries = modifier_type_map[modifier_type]
    for entry in entries:
        entry.update({"Bid Modifier": "1.0"})

    csv_example_file = StringIO.StringIO()
    writer = csv.DictWriter(csv_example_file, csv_columns, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(entries)
    csv_example_file.seek(0)
    return csv_example_file


def make_bulk_csv_example_file():
    def sub_file_generator():
        for modifier_type in constants.BidModifierType.get_all():
            yield make_csv_example_file(modifier_type)

    return helpers.create_bulk_csv_file(sub_file_generator())


def _write_upload_history(ad_group, number_of_deleted, number_of_created, user=None):
    messages = ["Uploaded bid modifiers."]

    if number_of_deleted > 0:
        messages.append("Removed %s bid modifier%s." % (number_of_deleted, "s" if number_of_deleted > 1 else ""))
    if number_of_created > 0:
        messages.append("Created %s bid modifier%s." % (number_of_created, "s" if number_of_created > 1 else ""))

    ad_group.write_history(
        " ".join(messages), user=user, action_type=dash_constants.HistoryActionType.BID_MODIFIER_UPDATE
    )


def _filter_bid_modifiers_by_user_access(bid_modifiers_qs, user, permission):
    return bid_modifiers_qs.filter_by_entity_permission(user, permission)


def _get_constant_examples(target_column_name, constant, excluded=[]):
    return [
        {target_column_name: constant.get_name(constant_value)}
        for constant_value in sorted(constant.get_all(), key=lambda x: (x is None, x))
        if constant_value not in excluded
    ]
