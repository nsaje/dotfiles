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
                                     campaign_settings, account, account_settings, include_global=True):

    blacklist = set([ad_group.default_blacklist_id, campaign.default_blacklist_id, account.default_blacklist_id])
    blacklist |= set(ad_group_settings.blacklist_publisher_groups)
    blacklist |= set(campaign_settings.blacklist_publisher_groups)
    blacklist |= set(account_settings.blacklist_publisher_groups)
    if include_global:
        blacklist |= set([get_global_blacklist().id])
    blacklist = [x for x in blacklist if x]

    whitelist = set([ad_group.default_whitelist_id, campaign.default_whitelist_id, account.default_whitelist_id])
    whitelist |= set(ad_group_settings.whitelist_publisher_groups)
    whitelist |= set(campaign_settings.whitelist_publisher_groups)
    whitelist |= set(account_settings.whitelist_publisher_groups)
    whitelist = [x for x in whitelist if x]

    return blacklist, whitelist


def get_default_publisher_group_targeting_dict():
    return {
        'ad_group': {
            'included': set(),
            'excluded': set(),
        },
        'campaign': {
            'included': set(),
            'excluded': set(),
        },
        'account': {
            'included': set(),
            'excluded': set(),
        },
        'global': {
            'excluded': set([get_global_blacklist().id]),
        },
    }


def get_publisher_group_targeting_dict(ad_group, ad_group_settings, campaign,
                                       campaign_settings, account, account_settings):
    d = get_default_publisher_group_targeting_dict()
    d.update({
        'ad_group': {
            'included': _get_whitelists(ad_group, ad_group_settings),
            'excluded': _get_blacklists(ad_group, ad_group_settings),
        },
        'campaign': {
            'included': _get_whitelists(campaign, campaign_settings),
            'excluded': _get_blacklists(campaign, campaign_settings),
        },
        'account': {
            'included': _get_whitelists(account, account_settings),
            'excluded': _get_blacklists(account, account_settings),
        }
    })
    return d


def get_publisher_list_level(entry, targeting):
    if entry.publisher_group_id in targeting['ad_group']['included'] | targeting['ad_group']['excluded']:
        return constants.PublisherBlacklistLevel.ADGROUP
    elif entry.publisher_group_id in targeting['campaign']['included'] | targeting['campaign']['excluded']:
        return constants.PublisherBlacklistLevel.CAMPAIGN
    elif entry.publisher_group_id in targeting['account']['included'] | targeting['account']['excluded']:
        return constants.PublisherBlacklistLevel.ACCOUNT
    elif entry.publisher_group_id in targeting['global']['excluded']:
        return constants.PublisherBlacklistLevel.GLOBAL
    return None


def _get_blacklists(obj, obj_settings):
    return set(x for x in [obj.default_blacklist_id] + obj_settings.blacklist_publisher_groups if x)


def _get_whitelists(obj, obj_settings):
    return set(x for x in [obj.default_whitelist_id] + obj_settings.whitelist_publisher_groups if x)


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


def create_publisher_id(publisher, source_id):
    return u'__'.join((publisher, unicode(source_id or '')))


def dissect_publisher_id(publisher_id):
    publisher, source_id = publisher_id.rsplit(u'__', 1)
    return publisher, int(source_id) if source_id else None
