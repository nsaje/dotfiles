import copy
import os
import random
import string

from django.conf import settings

import utils.exc
from core import models
from utils import csv_utils
from utils import s3helpers
from utils import zlogging

from .models import validate_placement

logger = zlogging.getLogger(__name__)

OUTBRAIN_AGENCY = 55


def get_example_csv_content(include_placement=False):
    if include_placement:
        columns = ["Publisher", "Placement (optional)", "Source (optional)"]
        content = [
            {"Publisher": "example.com", "Placement (optional)": None, "Source (optional)": None},
            {"Publisher": "some.example.com", "Placement (optional)": None, "Source (optional)": None},
        ]
    else:
        columns = ["Publisher", "Source (optional)"]
        content = [
            {"Publisher": "example.com", "Source (optional)": None},
            {"Publisher": "some.example.com", "Source (optional)": None},
        ]

    return csv_utils.dictlist_to_csv(columns, content)


def get_csv_content(publisher_group_entries, include_placement=False, agency=None, account=None):
    return csv_utils.tuplelist_to_csv(
        _get_rows_generator(
            publisher_group_entries, include_placement=include_placement, agency=agency, account=account
        )
    )


def get_entries_errors_csv_content(entry_dicts, include_placement=False, agency=None, account=None):
    return csv_utils.tuplelist_to_csv(
        _get_error_rows_generator(entry_dicts, include_placement=include_placement, agency=agency, account=account)
    )


def _get_rows_generator(publisher_group_entries, include_placement=False, agency=None, account=None):
    entries_list = list(publisher_group_entries.order_by("publisher"))

    if account is not None:
        is_outbrain = account.agency is not None and account.agency.id == OUTBRAIN_AGENCY
    elif agency is not None:
        is_outbrain = agency.id == OUTBRAIN_AGENCY

    add_outbrain_publisher_id = is_outbrain and any(
        (
            entry.outbrain_publisher_id
            or entry.outbrain_section_id
            or entry.outbrain_amplify_publisher_id
            or entry.outbrain_engage_publisher_id
        )
        for entry in entries_list
    )
    include_placement = include_placement or any(entry.placement for entry in entries_list)

    headers = ["Publisher", "Source"]
    if include_placement:
        headers.insert(1, "Placement")

    if add_outbrain_publisher_id:
        headers.append("Outbrain Publisher Id")
        headers.append("Outbrain Section Id")
        headers.append("Outbrain Amplify Publisher Id")
        headers.append("Outbrain Engage Publisher Id")
    yield headers

    for entry in entries_list:
        row = [entry.publisher, entry.source.get_clean_slug() if entry.source else None]
        if include_placement:
            row.insert(1, entry.placement if entry.placement else None)

        if add_outbrain_publisher_id:
            row.append(entry.outbrain_publisher_id)
            row.append(entry.outbrain_section_id)
            row.append(entry.outbrain_amplify_publisher_id)
            row.append(entry.outbrain_engage_publisher_id)
        yield row


def _get_error_rows_generator(entry_dicts, include_placement=False, agency=None, account=None):
    if account is not None:
        is_outbrain = account.agency is not None and account.agency.id == OUTBRAIN_AGENCY
    elif agency is not None:
        is_outbrain = agency.id == OUTBRAIN_AGENCY
    add_outbrain_publisher_id = is_outbrain and any(
        (
            "outbrain_publisher_id" in entry_dict
            or "outbrain_section_id" in entry_dict
            or "outbrain_amplify_publisher_id" in entry_dict
            or "outbrain_engage_publisher_id" in entry_dict
        )
        for entry_dict in entry_dicts
    )

    headers = ["Publisher", "Source", "Error"]
    if include_placement:
        headers.insert(1, "Placement")

    if add_outbrain_publisher_id:
        headers.insert(-1, "Outbrain Publisher Id")
        headers.insert(-1, "Outbrain Section Id")
        headers.insert(-1, "Outbrain Amplify Publisher Id")
        headers.insert(-1, "Outbrain Engage Publisher Id")
    yield headers

    for entry in entry_dicts:
        row = [entry.get("publisher"), entry.get("source"), entry.get("error")]
        if include_placement:
            row.insert(1, entry.get("placement"))
        if add_outbrain_publisher_id:
            row.insert(-1, entry.get("outbrain_publisher_id"))
            row.insert(-1, entry.get("outbrain_section_id"))
            row.insert(-1, entry.get("outbrain_amplify_publisher_id"))
            row.insert(-1, entry.get("outbrain_engage_publisher_id"))
        yield row


def validate_entries(entry_dicts, include_placement=False):
    validated_entry_dicts = []
    sources_by_slug = {x.get_clean_slug(): x for x in models.Source.objects.all()}

    for entry in entry_dicts:
        if entry.get("publisher") == "":
            entry.update({"publisher": None})
        if entry.get("placement") == "":
            entry.update({"placement": None})

        # these two will get modified for validation purposes
        publisher = entry.get("publisher")
        source_slug = entry.get("source")

        error = []

        if publisher:
            prefixes = ("http://", "https://")
            if any(publisher.startswith(x) for x in prefixes):
                error.append("Remove the following prefixes: http, https")

            # these were already validated, remove so they won't cause false errors in further validation
            for prefix in prefixes:
                publisher = publisher.replace(prefix, "")

            if "/" in publisher:
                error.append("'/' should not be used")
        else:
            error.append("Publisher is required")

        try:
            validate_placement(entry.get("placement"))
        except utils.exc.ValidationError as e:
            error.append(str(e))

        validated_entry = copy.copy(entry)
        if "error" in validated_entry:
            del validated_entry["error"]

        if source_slug:
            if source_slug.lower() not in sources_by_slug:
                error.append("Unknown source")
        else:
            validated_entry["source"] = None

        if error:
            validated_entry["error"] = "; ".join(error)
        validated_entry_dicts.append(validated_entry)
    return validated_entry_dicts


def clean_entry_sources(entry_dicts):
    sources_by_slug = {x.get_clean_slug(): x for x in models.Source.objects.all()}
    for entry in entry_dicts:
        if "source" not in entry:
            entry["source"] = ""
        entry["source"] = sources_by_slug.get(entry["source"].lower())


def save_entries_errors_csv(entry_dicts, include_placement=False, agency=None, account=None):
    csv_content = get_entries_errors_csv_content(entry_dicts, agency=agency, account=account)
    csv_content = get_entries_errors_csv_content(
        entry_dicts, include_placement=include_placement, agency=agency, account=account
    )
    csv_key = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(64))
    s3_helper = s3helpers.S3Helper(settings.S3_BUCKET_PUBLISHER_GROUPS)
    if account is not None:
        s3_helper.put(
            os.path.join("publisher_group_errors", "account_{}".format(account.id), csv_key + ".csv"), csv_content
        )
    elif agency is not None:
        s3_helper.put(
            os.path.join("publisher_group_errors", "agency_{}".format(agency.id), csv_key + ".csv"), csv_content
        )

    return csv_key
