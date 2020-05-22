import re

from django.db.models import QuerySet

OUTBRAIN_SOURCE_ID = 3
PLACEMENT_SEPARATOR = "__"


class InvalidLookupKeyFormat(ValueError):
    pass


def publisher_exchange(source):
    """
    This is a oneliner that is often repeated and will be replaced
    by something decent once we start using source id's in Redshift
    instead of exchange strings
    """
    return source and source.tracking_slug.replace("b1_", "")


def is_publisher_domain(raw_str):
    # keep
    if raw_str is None:
        return False
    return re.search(r"\.[a-z]+$", raw_str.lower()) is not None


def get_publisher_domain_link(raw_str):
    # keep
    if is_publisher_domain(raw_str):
        return "http://" + raw_str
    return ""


def create_publisher_id(publisher, source_id):
    return "__".join((publisher, str(source_id or "")))


def dissect_publisher_id(publisher_id):
    publisher, source_id = publisher_id.rsplit("__", 1)
    if source_id == "all":
        return publisher, source_id

    try:
        return publisher, int(source_id) if source_id else None
    except ValueError:
        raise InvalidLookupKeyFormat("PublisherId: {}".format(publisher_id))


def inflate_publisher_id_source(publisher_id, source_ids):
    publisher, source_id = dissect_publisher_id(publisher_id)
    if source_id is not None:
        return [publisher_id]

    return [create_publisher_id(publisher, x) for x in source_ids]


def create_placement_id(publisher, source_id, placement):
    publisher_source_id = create_publisher_id(publisher, source_id)
    return publisher_source_id + PLACEMENT_SEPARATOR + (placement or "")


def dissect_placement_id(publisher_source_placement_id):
    if PLACEMENT_SEPARATOR not in publisher_source_placement_id:
        raise InvalidLookupKeyFormat("PublisherPlacement: {}".format(publisher_source_placement_id))

    publisher_source_id, placement = publisher_source_placement_id.rsplit(PLACEMENT_SEPARATOR, 1)

    if "__" not in publisher_source_id:
        raise InvalidLookupKeyFormat("PublisherPlacement: {}".format(publisher_source_placement_id))

    publisher, source_id = dissect_publisher_id(publisher_source_id)
    return publisher, source_id, placement or None


def strip_prefix(publisher, prefixes=("http://", "https://")):
    for prefix in prefixes:
        publisher = publisher.replace(prefix, "")
    return publisher


def is_subdomain_match(listed_publisher, publisher):
    listed_split = listed_publisher.split(".")
    listed_split.reverse()

    publisher_split = strip_prefix(publisher).split(".")
    publisher_split.reverse()

    for i, part in enumerate(listed_split):
        if len(publisher_split) < i + 1:
            return False

        if listed_split[i] != publisher_split[i]:
            return False

    return True


def all_subdomains(publisher):
    parts = publisher.split(".")
    return [".".join(parts[i:]) for i in range(1, len(parts))]


class PublisherIdLookupMap(object):
    def _filter_publisher_group_entries(self, entries):
        if isinstance(entries, QuerySet):
            return entries.filter_publisher_or_placement(False)

        return [e for e in entries if e.placement is None]

    def _add_entry_to_map(self, entry):
        publisher_name = entry.publisher.strip().lower()
        if entry.source_id:
            self._map[create_publisher_id(publisher_name, entry.source_id)] = entry
        else:
            self._map[create_publisher_id(publisher_name, "all")] = entry

    def _add_to_map(self, entries):
        for entry in self._filter_publisher_group_entries(entries):
            self._add_entry_to_map(entry)

    def __init__(self, dominant_entries_qs, secondary_entries_qs=None):
        self._map = {}

        # Blacklisted entry has priority before whitelisted entries. That is why when an entry is blacklisted and
        # whitelisted at the same time, take into account only the blacklisted one. By first inserting whitelisted
        # entries we ensure that entries that target the same publisher will get overwritten in the map by
        # entries from the blacklist.
        # From the case above blacklist consists of dominant entries, whitelist from secondary ones.
        if secondary_entries_qs is not None:
            self._add_to_map(secondary_entries_qs)
        self._add_to_map(dominant_entries_qs)

    def _find_publisher_group_entry_subdomains(self, publisher_id):
        # check for exact match
        entry = self._map.get(publisher_id)
        if entry is not None:
            return entry

        # find subdomain match
        for subdomain in all_subdomains(publisher_id):
            entry = self._map.get(subdomain)
            if entry is not None and entry.include_subdomains and entry.source_id != OUTBRAIN_SOURCE_ID:
                return entry

        return None

    def __getitem__(self, publisher_id):
        publisher, source_id = dissect_publisher_id(publisher_id)
        publisher = publisher.strip().lower()

        publisher_source = create_publisher_id(publisher, source_id)
        entry = self._find_publisher_group_entry_subdomains(publisher_source)
        if entry is not None:
            return entry

        publisher_all = create_publisher_id(publisher, "all")
        entry = self._find_publisher_group_entry_subdomains(publisher_all)
        if entry is not None:
            return entry

        return None

    def __contains__(self, publisher_id):
        return self[publisher_id] is not None


class PublisherPlacementLookupMap(PublisherIdLookupMap):
    def _filter_publisher_group_entries(self, entries):
        if isinstance(entries, QuerySet):
            return entries.filter_publisher_or_placement(True)

        return [e for e in entries if e.placement is not None]

    def _add_entry_to_map(self, entry):
        publisher_name = entry.publisher.strip().lower()
        if entry.source_id:
            self._map[create_placement_id(publisher_name, entry.source_id, entry.placement)] = entry
        else:
            self._map[create_placement_id(publisher_name, "all", entry.placement)] = entry

    def __getitem__(self, publisher_id):
        publisher, source_id, placement = dissect_placement_id(publisher_id)
        publisher = publisher.strip().lower()

        publisher_source_placement = create_placement_id(publisher, source_id, placement)
        entry = self._find_publisher_group_entry_subdomains(publisher_source_placement)
        if entry is not None:
            return entry

        publisher_all_placement = create_placement_id(publisher, "all", placement)
        entry = self._find_publisher_group_entry_subdomains(publisher_all_placement)
        if entry is not None:
            return entry

        return None
