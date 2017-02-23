import re

from dash import models

from django.db.models import Q


def prepare_publishers_for_rs_query(ad_group):
    """
    Fetch all blacklisted publisher entries for use with
    filtering only blacklisted or non blacklisted publisher statistics
    """
    # fetch blacklisted status from db
    adg_pub_blacklist_qs = models.PublisherBlacklist.objects.filter(
        Q(ad_group=ad_group) |
        Q(campaign=ad_group.campaign) |
        Q(account=ad_group.campaign.account)
    )
    adg_blacklisted_publishers = adg_pub_blacklist_qs.iterator()
    adg_blacklisted_publishers = map(lambda entry: {
        'domain': entry.name,
        'adgroup_id': ad_group.id,
        'exchange': publisher_exchange(entry.source),
    }, adg_blacklisted_publishers)

    # include global, campaign and account stats if they exist
    global_pub_blacklist_qs = models.PublisherBlacklist.objects.filter(
        everywhere=True
    )
    adg_blacklisted_publishers.extend(map(lambda pub_bl: {
        'domain': pub_bl.name
    }, global_pub_blacklist_qs)
    )
    return adg_blacklisted_publishers


def publisher_exchange(source):
    # keep
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
