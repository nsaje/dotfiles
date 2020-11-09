import csv
import gzip
import io
import json
import os
from collections import defaultdict

from django.conf import settings
from django.db.models import F

from dash import models
from utils import dates_helper
from utils import s3helpers
from utils import zlogging

logger = zlogging.getLogger(__name__)


STATUS_BLACKLISTED = 2
FILENAME_SAFE_TIME_FORMAT = "%Y-%m-%dT%H-%M-%S.%fZ"
KEEP_LAST_UPDATES = 3

B1_S3_PUBLISHER_GROUPS_PREFIX = "publishergroups_v2"

ANNOTATION_QUALIFIED_PUBLISHER_GROUPS = set([16922])


def tree():
    return defaultdict(tree)


def sync_publisher_groups():
    s3_helper = s3helpers.S3Helper(settings.S3_BUCKET_B1_DATA_USE)
    timestamp = dates_helper.utc_now().strftime(FILENAME_SAFE_TIME_FORMAT)

    logger.info("Getting publisher group data")
    data = _get_data()

    logger.info("Marshaling data")
    content = _marshal(data)

    logger.info("Uploading data")
    _put_to_s3(s3_helper, timestamp, content)

    logger.info("Removing old data")
    _remove_old_publisher_groups_files(s3_helper)

    logger.info("Done")


def _get_data():
    publisher_group_accounts = {
        g["pk"]: g["account_id"]
        for g in models.PublisherGroup.objects.filter_by_active_candidate_adgroups().values("pk", "account_id")
    }
    logger.info("Got publisher groups")

    publisher_groups_entries = (
        models.PublisherGroupEntry.objects.filter(publisher_group_id__in=publisher_group_accounts.keys())
        .order_by("pk")
        .annotate(source_slug=F("source__bidder_slug"))
        .values(
            "id",
            "source_slug",
            "publisher_group_id",
            "include_subdomains",
            "outbrain_publisher_id",
            "outbrain_section_id",
            "outbrain_amplify_publisher_id",
            "outbrain_engage_publisher_id",
            "publisher",
            "placement",
        )
    )

    annotations_lookup_tree = tree()
    groups_lookup_tree = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    subdomain_groups_lookup_tree = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    for entry in publisher_groups_entries.iterator():
        entry["account_id"] = publisher_group_accounts[entry["publisher_group_id"]]
        _sanitize_names(entry)
        _insert_into_lookup_trees(entry, groups_lookup_tree, subdomain_groups_lookup_tree)
        _insert_into_annotations_lookup_tree(entry, annotations_lookup_tree)

    return {
        "publisherGroupsLookupTree": groups_lookup_tree,
        "subdomainPublisherGroupsLookupTree": subdomain_groups_lookup_tree,
        "annotationsLookupTree": annotations_lookup_tree,
        "syncedPublisherGroupIds": list(publisher_group_accounts.keys()),
    }


def _sanitize_names(entry):
    entry["publisher"] = entry["publisher"].strip().lower()


def _insert_into_lookup_trees(entry, groups_lookup_tree, subdomain_groups_lookup_tree):
    source_slug = entry["source_slug"] or ""
    publisher = entry["publisher"]
    placement = entry.get("placement") or ""
    publisher_group_id = str(entry["publisher_group_id"])

    groups_lookup_tree[source_slug][publisher][placement].append(publisher_group_id)
    if entry.get("include_subdomains"):
        subdomain_groups_lookup_tree[source_slug][publisher][placement].append(publisher_group_id)


def _insert_into_annotations_lookup_tree(entry, annotations_lookup_tree):
    if entry["publisher_group_id"] not in ANNOTATION_QUALIFIED_PUBLISHER_GROUPS:
        return

    annotation = {}
    outbrain_publisher_id = entry.get("outbrain_publisher_id")
    if outbrain_publisher_id:
        annotation["outbrainPublisherID"] = outbrain_publisher_id

    outbrain_section_id = entry.get("outbrain_section_id")
    if outbrain_section_id:
        annotation["outbrainSectionID"] = outbrain_section_id

    outbrain_amplify_publisher_id = entry.get("outbrain_amplify_publisher_id")
    if outbrain_amplify_publisher_id:
        annotation["outbrainAmplifyPublisherID"] = outbrain_amplify_publisher_id

    outbrain_engage_publisher_id = entry.get("outbrain_engage_publisher_id")
    if outbrain_engage_publisher_id:
        annotation["outbrainEngagePublisherID"] = outbrain_engage_publisher_id

    if not annotation:
        return

    if not entry["account_id"]:
        raise Exception("Annotation defined without accound id! %s" % annotation)
    annotations_lookup_tree[entry["account_id"]][entry["publisher"]][entry["source_slug"] or ""] = annotation


def _marshal(data):
    content = ""
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_ALL, lineterminator="\n")

    for group_key in sorted(data.keys()):
        num_of_rows = 0

        if group_key in ["publisherGroupsLookupTree", "subdomainPublisherGroupsLookupTree"]:
            for exchange_key, exchange_value in data[group_key].items():
                for domain_key, domain_value in exchange_value.items():
                    for placement_key, placement_value in domain_value.items():
                        writer.writerow([exchange_key, domain_key, placement_key, json.dumps(placement_value)])
                        num_of_rows += 1

        elif group_key == "syncedPublisherGroupIds":
            for syncedPublisherGroupId in sorted(data[group_key]):
                writer.writerow([syncedPublisherGroupId])
                num_of_rows += 1

        elif group_key == "annotationsLookupTree":
            for key in data[group_key].keys():
                for domain_key, domain_value in data[group_key][key].items():
                    for exchange_key, exchange_value in domain_value.items():
                        writer.writerow([key, domain_key, exchange_key, json.dumps(exchange_value)])
                        num_of_rows += 1

        content += group_key + ":" + str(num_of_rows) + "\n"

    content += output.getvalue()

    return content


def _put_to_s3(s3_helper, timestamp, content):
    s3_helper = s3helpers.S3Helper(settings.S3_BUCKET_B1_DATA_USE)
    timestamp = dates_helper.utc_now().strftime(FILENAME_SAFE_TIME_FORMAT)

    path = os.path.join(B1_S3_PUBLISHER_GROUPS_PREFIX, timestamp, "full", timestamp + ".gz")
    s3_helper.put(path, gzip.compress(content.encode()))


def _remove_old_publisher_groups_files(s3_helper):
    existing_files = list(reversed(sorted(k.name for k in s3_helper.list(B1_S3_PUBLISHER_GROUPS_PREFIX + "/"))))
    for path in existing_files[KEEP_LAST_UPDATES + 1 :]:
        s3_helper.delete(path)
