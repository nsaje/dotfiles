import re


def publisher_exchange(source):
    """
    This is a oneliner that is often repeated and will be replaced
    by something decent once we start using source id's in Redshift
    instead of exchange strings
    """
    return source and source.tracking_slug.replace('b1_', '')


def is_publisher_domain(raw_str):
    # keep
    if raw_str is None:
        return False
    return re.search("\.[a-z]+$", raw_str.lower()) is not None


def get_publisher_domain_link(raw_str):
    # keep
    if is_publisher_domain(raw_str):
        return "http://" + raw_str
    return ""


def create_publisher_id(publisher, source_id):
    return u'__'.join((publisher, unicode(source_id or '')))


def dissect_publisher_id(publisher_id):
    publisher, source_id = publisher_id.rsplit(u'__', 1)
    if source_id == 'all':
        return publisher, source_id
    return publisher, int(source_id) if source_id else None


def inflate_publisher_id_source(publisher_id, source_ids):
    publisher, source_id = dissect_publisher_id(publisher_id)
    if source_id is not None:
        return [publisher_id]

    return [create_publisher_id(publisher, x) for x in source_ids]


def strip_prefix(publisher, prefixes=('http://', 'https://')):
    for prefix in prefixes:
        publisher = publisher.replace(prefix, '')
    return publisher


def is_subdomain_match(listed_publisher, publisher):
    listed_split = listed_publisher.split('.')
    listed_split.reverse()

    publisher_split = strip_prefix(publisher).split('.')
    publisher_split.reverse()

    for i, part in enumerate(listed_split):
        if len(publisher_split) < i + 1:
            return False

        if listed_split[i] != publisher_split[i]:
            return False

    return True


def all_subdomains(publisher):
    parts = publisher.split('.')
    return ['.'.join(parts[i:]) for i in range(1, len(parts))]


class PublisherIdLookupMap(object):
    def _add_to_map(self, entries):
        for entry in entries:
            publisher_name = entry.publisher.strip().lower()
            if entry.source_id:
                self._map[create_publisher_id(publisher_name, entry.source_id)] = entry
            else:
                self._map[create_publisher_id(publisher_name, 'all')] = entry

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
            if entry is not None and entry.include_subdomains:
                return entry

        return None

    def __getitem__(self, publisher_id):
        publisher, source_id = dissect_publisher_id(publisher_id)
        publisher = publisher.strip().lower()

        publisher_source = create_publisher_id(publisher, source_id)
        entry = self._find_publisher_group_entry_subdomains(publisher_source)
        if entry is not None:
            return entry

        publisher_all = create_publisher_id(publisher, 'all')
        entry = self._find_publisher_group_entry_subdomains(publisher_all)
        if entry is not None:
            return entry

        return None

    def __contains__(self, publisher_id):
        return self[publisher_id] is not None
