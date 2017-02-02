from django.conf import settings
from django.db import transaction
from django.db.models import Q
from dash import models
from dash import constants


class PublisherGroupTargetingException(Exception):
    pass


def get_global_blacklist():
    # Publisher group with this id should always exist
    return models.PublisherGroup.objects.get(pk=settings.GLOBAL_BLACKLIST_ID)


def get_blacklist_publisher_group(obj, create_if_none=False, request=None):
    if obj is None:
        return get_global_blacklist()

    publisher_group = obj.default_blacklist
    if publisher_group is None and create_if_none:
        with transaction.atomic():
            publisher_group = models.PublisherGroup(
                name=obj.get_default_blacklist_name(),
                account=obj.get_account())
            publisher_group.save(request)
            obj.default_blacklist = publisher_group
            obj.save(request)

    return publisher_group


def get_whitelist_publisher_group(obj, create_if_none=False, request=None):
    if obj is None:
        raise PublisherGroupTargetingException("Whitelisting not supported on global level")

    with transaction.atomic():
        publisher_group = obj.default_whitelist
        if publisher_group is None and create_if_none:
            publisher_group = models.PublisherGroup(
                name=obj.get_default_whitelist_name(),
                account=obj.get_account())
            publisher_group.save(request)
            obj.default_whitelist = publisher_group
            obj.save(request)

    return publisher_group


def can_user_handle_publishers(user, obj):
    if (isinstance(obj, models.Account) or isinstance(obj, models.Campaign)) and \
       not user.has_perm('zemauth.can_access_campaign_account_publisher_blacklist_status'):
        return False
    if obj is None and not user.has_perm('zemauth.can_access_global_publisher_blacklist_status'):
        return False
    return True


def concat_publisher_group_targeting(ad_group, ad_group_settings, campaign,
                                     campaign_settings, account, account_settings):
    blacklist = set([ad_group.default_blacklist_id, campaign.default_blacklist_id, account.default_blacklist_id])
    blacklist |= set(ad_group_settings.blacklist_publisher_groups)
    blacklist |= set(campaign_settings.blacklist_publisher_groups)
    blacklist |= set(account_settings.blacklist_publisher_groups)
    blacklist |= set([get_global_blacklist().id])
    blacklist = [x for x in blacklist if x]

    whitelist = set([ad_group.default_whitelist_id, campaign.default_whitelist_id, account.default_whitelist_id])
    whitelist |= set(ad_group_settings.whitelist_publisher_groups)
    whitelist |= set(campaign_settings.whitelist_publisher_groups)
    whitelist |= set(account_settings.whitelist_publisher_groups)
    whitelist = [x for x in whitelist if x]

    return blacklist, whitelist


def handle_publishers(request, entry_dicts, obj, status):
    if status == constants.PublisherTargetingStatus.BLACKLISTED:
        blacklist_publishers(request, entry_dicts, obj)
    elif status == constants.PublisherTargetingStatus.WHITELISTED:
        whitelist_publishers(request, entry_dicts, obj)
    else:
        unlist_publishers(request, entry_dicts, obj)


@transaction.atomic
def blacklist_publishers(request, entry_dicts, obj):
    publisher_group = get_blacklist_publisher_group(obj, create_if_none=True, request=request)

    unlist_publishers(request, entry_dicts, obj)

    entries = _create_entries(entry_dicts, publisher_group)
    models.PublisherGroupEntry.objects.bulk_create(entries)


@transaction.atomic
def whitelist_publishers(request, entry_dicts, obj):
    publisher_group = get_whitelist_publisher_group(obj, create_if_none=True, request=request)

    unlist_publishers(request, entry_dicts, obj)

    entries = _create_entries(entry_dicts, publisher_group)
    models.PublisherGroupEntry.objects.bulk_create(entries)


@transaction.atomic
def unlist_publishers(request, entry_dicts, obj):
    publisher_group = get_blacklist_publisher_group(obj)
    selected_entries = models.PublisherGroupEntry.objects.filter(publisher_group=publisher_group)\
                                                         .filter(_create_domain_constraints(entry_dicts))
    selected_entries.delete()

    try:
        publisher_group = get_whitelist_publisher_group(obj)
        selected_entries = models.PublisherGroupEntry.objects.filter(publisher_group=publisher_group)\
                                                             .filter(_create_domain_constraints(entry_dicts))
        selected_entries.delete()
    except PublisherGroupTargetingException:
        # pass if global level
        pass


def _create_entries(entry_dicts, publisher_group):
    entries = []
    for entry in entry_dicts:
        entries.append(models.PublisherGroupEntry(
            publisher=entry['publisher'],
            source=entry['source'],
            include_subdomains=entry['include_subdomains'],
            publisher_group=publisher_group,
        ))
    return entries


def _create_domain_constraints(entry_dicts):
    constraints = []
    for entry in entry_dicts:
        constraints.append({
            'publisher': entry['publisher'],
            'source': entry['source']
        })

    q = Q(**constraints.pop())
    for c in constraints:
        q |= Q(**c)
    return q
