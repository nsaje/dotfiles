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
