from collections import defaultdict
import logging
import re
from decimal import Decimal

from django.conf import settings
from django.db import transaction

from dash import constants, cpc_constraints, history_helpers, models
from dash.views import helpers
from utils import email_helper

logger = logging.getLogger(__name__)

OUTBRAIN_CPC_CONSTRAINT_LIMIT = 30
OUTBRAIN_CPC_CONSTRAINT_MIN = Decimal('0.65')


class PublisherGroupTargetingException(Exception):
    pass


def get_global_blacklist():
    # Publisher group with this id should always exist
    return models.PublisherGroup.objects.get(pk=settings.GLOBAL_BLACKLIST_ID)


def get_blacklist_publisher_group(obj, create_if_none=False, request=None):
    """
    Gets default blacklist publisher group or (optionally) creates a new one.
    """

    if obj is None:
        return get_global_blacklist()

    publisher_group = obj.default_blacklist
    if publisher_group is None and create_if_none:
        with transaction.atomic():
            publisher_group = models.PublisherGroup.objects.create(
                request,
                name=obj.get_default_blacklist_name(),
                account=obj.get_account(),
                default_include_subdomains=True,
                implicit=True)
            obj.default_blacklist = publisher_group
            obj.save(request)

    return publisher_group


def get_whitelist_publisher_group(obj, create_if_none=False, request=None):
    """
    Gets default whitelist publisher group or (optionally) creates a new one.
    """

    if obj is None:
        raise PublisherGroupTargetingException("Whitelisting not supported on global level")

    with transaction.atomic():
        publisher_group = obj.default_whitelist
        if publisher_group is None and create_if_none:
            publisher_group = models.PublisherGroup.objects.create(
                request,
                name=obj.get_default_whitelist_name(),
                account=obj.get_account(),
                default_include_subdomains=True,
                implicit=True)
            obj.default_whitelist = publisher_group
            obj.save(request)

    return publisher_group


def can_user_handle_publisher_listing_level(user, obj):
    if (isinstance(obj, models.Account) or isinstance(obj, models.Campaign)) and \
       not user.has_perm('zemauth.can_access_campaign_account_publisher_blacklist_status'):
        return False
    if obj is None and not user.has_perm('zemauth.can_access_global_publisher_blacklist_status'):
        return False
    return True


def concat_publisher_group_targeting(ad_group, ad_group_settings, campaign,
                                     campaign_settings, account, account_settings, include_global=True):

    blacklist = set()
    whitelist = set()

    if ad_group:
        blacklist |= _get_blacklists(ad_group, ad_group_settings)
        whitelist |= _get_whitelists(ad_group, ad_group_settings)
    if campaign:
        blacklist |= _get_blacklists(campaign, campaign_settings)
        whitelist |= _get_whitelists(campaign, campaign_settings)
    if account:
        blacklist |= _get_blacklists(account, account_settings)
        whitelist |= _get_whitelists(account, account_settings)

    if include_global:
        blacklist |= set([get_global_blacklist().id])

    blacklist = sorted([x for x in blacklist if x])
    whitelist = sorted([x for x in whitelist if x])

    return blacklist, whitelist


def get_publisher_group_targeting_multiple_entities(accounts, campaigns, ad_groups, include_global=True):
    whitelist = set()
    blacklist = set()

    def gettargeting():
        return {
            'included': set(),
            'excluded': set(),
        }

    targeting = {
        'ad_group': defaultdict(gettargeting),
        'campaign': defaultdict(gettargeting),
        'account': defaultdict(gettargeting),
        'global': {
            'excluded': set([get_global_blacklist().id]) if include_global else set(),
        },
    }
    if include_global:
        blacklist = set([get_global_blacklist().id])

    def fill_up(any_settings, related_field):
        for x in any_settings:
            current = set(x.blacklist_publisher_groups) | set([getattr(x, related_field).default_blacklist_id])
            current = set(x for x in current if x)

            blacklist.update(current)
            targeting[related_field][getattr(x, related_field).id]['excluded'].update(current)

            current = set(x.whitelist_publisher_groups) | set([getattr(x, related_field).default_whitelist_id])
            current = set(x for x in current if x)

            whitelist.update(current)
            targeting[related_field][getattr(x, related_field).id]['included'].update(current)

    if accounts is not None:
        accounts_settings = models.AccountSettings.objects.filter(
            account__in=accounts
        ).group_current_settings().prefetch_related('account')
        fill_up(accounts_settings, 'account')

    if campaigns is not None:
        campaigns_settings = models.CampaignSettings.objects.filter(
            campaign__in=campaigns
        ).group_current_settings().prefetch_related('campaign')
        fill_up(campaigns_settings, 'campaign')

    if ad_groups is not None:
        ad_groups_settings = models.AdGroupSettings.objects.filter(
            ad_group__in=ad_groups
        ).group_current_settings().prefetch_related('ad_group')
        fill_up(ad_groups_settings, 'ad_group')

    return blacklist, whitelist, targeting


def get_default_publisher_group_targeting_dict(include_global=True):
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
            'excluded': set([get_global_blacklist().id]) if include_global else set(),
        },
    }


def get_publisher_group_targeting_dict(ad_group, ad_group_settings, campaign,
                                       campaign_settings, account, account_settings, include_global=True):
    d = get_default_publisher_group_targeting_dict(include_global)
    if ad_group is not None:
        d.update({
            'ad_group': {
                'included': _get_whitelists(ad_group, ad_group_settings),
                'excluded': _get_blacklists(ad_group, ad_group_settings),
            },
        })
    if campaign is not None:
        d.update({
            'campaign': {
                'included': _get_whitelists(campaign, campaign_settings),
                'excluded': _get_blacklists(campaign, campaign_settings),
            },
        })
    if account is not None:
        d.update({
            'account': {
                'included': _get_whitelists(account, account_settings),
                'excluded': _get_blacklists(account, account_settings),
            }
        })
    return d


def get_publisher_entry_list_level(entry, targeting):
    if entry.publisher_group_id in targeting['ad_group']['included'] | targeting['ad_group']['excluded']:
        return constants.PublisherBlacklistLevel.ADGROUP
    elif entry.publisher_group_id in targeting['campaign']['included'] | targeting['campaign']['excluded']:
        return constants.PublisherBlacklistLevel.CAMPAIGN
    elif entry.publisher_group_id in targeting['account']['included'] | targeting['account']['excluded']:
        return constants.PublisherBlacklistLevel.ACCOUNT
    elif entry.publisher_group_id in targeting['global']['excluded']:
        return constants.PublisherBlacklistLevel.GLOBAL
    raise PublisherGroupTargetingException("Publisher entry does not belong to specified targeting configuration")


def _get_blacklists(obj, obj_settings):
    """
    Concats default blacklist and publisher group targeting
    """

    return set(x for x in [obj.default_blacklist_id] + obj_settings.blacklist_publisher_groups if x)


def _get_whitelists(obj, obj_settings):
    """
    Concats default whitelist and publisher group targeting
    """

    return set(x for x in [obj.default_whitelist_id] + obj_settings.whitelist_publisher_groups if x)


def handle_publishers(request, entry_dicts, obj, status, enforce_cpc):
    if status == constants.PublisherTargetingStatus.BLACKLISTED:
        blacklist_publishers(request, entry_dicts, obj, enforce_cpc)
    elif status == constants.PublisherTargetingStatus.WHITELISTED:
        whitelist_publishers(request, entry_dicts, obj, enforce_cpc)
    else:
        unlist_publishers(request, entry_dicts, obj, enforce_cpc)


@transaction.atomic
def blacklist_publishers(request, entry_dicts, obj, enforce_cpc=False):
    publisher_group = get_blacklist_publisher_group(obj, create_if_none=True, request=request)

    # cpc constraints and history will be handled separately
    unlist_publishers(request, entry_dicts, obj, enforce_cpc=False, history=False)

    entries = _prepare_entries(entry_dicts, publisher_group)

    for entry in entries:
        validate_blacklist_entry(obj, entry)

    models.PublisherGroupEntry.objects.bulk_create(entries)

    apply_outbrain_account_constraints_if_needed(obj, enforce_cpc)

    ping_k1(obj)
    write_history(request, obj, entries, constants.PublisherTargetingStatus.BLACKLISTED)


@transaction.atomic
def whitelist_publishers(request, entry_dicts, obj, enforce_cpc=False):
    publisher_group = get_whitelist_publisher_group(obj, create_if_none=True, request=request)

    # cpc constraints and history will be handled separately
    unlist_publishers(request, entry_dicts, obj, enforce_cpc=False, history=False)

    entries = _prepare_entries(entry_dicts, publisher_group)
    models.PublisherGroupEntry.objects.bulk_create(entries)

    apply_outbrain_account_constraints_if_needed(obj, enforce_cpc)

    ping_k1(obj)
    write_history(request, obj, entries, constants.PublisherTargetingStatus.WHITELISTED)


@transaction.atomic
def unlist_publishers(request, entry_dicts, obj, enforce_cpc=False, history=True):
    publisher_group = get_blacklist_publisher_group(obj)
    selected_entries = models.PublisherGroupEntry.objects.filter(publisher_group=publisher_group)\
                                                         .filter_by_publisher_source(entry_dicts)
    if history and selected_entries.exists():
        write_history(request, obj, selected_entries,
                      constants.PublisherTargetingStatus.UNLISTED,
                      constants.PublisherTargetingStatus.BLACKLISTED)

    selected_entries.delete()

    try:
        publisher_group = get_whitelist_publisher_group(obj)
        selected_entries = models.PublisherGroupEntry.objects.filter(publisher_group=publisher_group)\
                                                             .filter_by_publisher_source(entry_dicts)
        if history and selected_entries.exists():
            write_history(request, obj, selected_entries,
                          constants.PublisherTargetingStatus.UNLISTED,
                          constants.PublisherTargetingStatus.WHITELISTED)

        selected_entries.delete()
        ping_k1(obj)
    except PublisherGroupTargetingException:
        # pass if global level
        pass

    apply_outbrain_account_constraints_if_needed(obj, enforce_cpc)


@transaction.atomic
def upsert_publisher_group(request, account_id, publisher_group_dict, entry_dicts):
    changes = {}

    include_subdomains = bool(publisher_group_dict.get('include_subdomains'))

    # update or create publisher group
    if publisher_group_dict.get('id'):
        publisher_group = helpers.get_publisher_group(request.user, account_id, publisher_group_dict['id'])
        history_action_type = constants.HistoryActionType.PUBLISHER_GROUP_UPDATE
        changes_text = "Publisher group \"{} [{}]\" updated".format(publisher_group.name, publisher_group.id)

        if include_subdomains != publisher_group.default_include_subdomains:
            changes['include_subdomains'] = (publisher_group.default_include_subdomains, include_subdomains)
            publisher_group.default_include_subdomains = include_subdomains

        if publisher_group.name != publisher_group_dict['name']:
            changes['name'] = (publisher_group.name, publisher_group_dict['name'])
            publisher_group.name = publisher_group_dict['name']

        publisher_group.save(request)
    else:
        publisher_group = models.PublisherGroup.objects.create(
            request,
            name=publisher_group_dict['name'],
            account=helpers.get_account(request.user, account_id),
            default_include_subdomains=include_subdomains,
            implicit=False)
        history_action_type = constants.HistoryActionType.PUBLISHER_GROUP_CREATE
        changes_text = "Publisher group \"{} [{}]\" created".format(publisher_group.name, publisher_group.id)

    # replace publishers
    if entry_dicts:
        changes['entries'] = [[], []]
        changes['entries'][0] = list(publisher_group.entries.all().values(
            'id', 'publisher', 'source__name', 'include_subdomains'))
        models.PublisherGroupEntry.objects.filter(publisher_group=publisher_group).delete()
        models.PublisherGroupEntry.objects.bulk_create(_prepare_entries(entry_dicts, publisher_group))
        changes['entries'][1] = list(publisher_group.entries.all().values(
            'id', 'publisher', 'source__name', 'include_subdomains'))

    if history_action_type == constants.HistoryActionType.PUBLISHER_GROUP_UPDATE and changes:
        changes_text += ", " + _get_changes_description(changes)

    # update entries
    for entry in publisher_group.entries.all():
        entry.include_subdomains = publisher_group.default_include_subdomains
        entry.save()

    # write history
    publisher_group.write_history(changes_text, changes, history_action_type, request.user)

    return publisher_group


def _get_changes_description(changes):
    texts = []
    if 'name' in changes:
        texts.append('name changed from "{}" to "{}"'.format(*changes['name']))
    if 'include_subdomains' in changes:
        texts.append('subdomains included changed from "{}" to "{}"'.format(*changes['include_subdomains']))
    if 'entries' in changes:
        texts.append('{} publishers replaced'.format(len(changes['entries'][1])))
    return ", ".join(texts)


def write_history(request, obj, entries, status, previous_status=None):
    if status == constants.PublisherTargetingStatus.UNLISTED and previous_status is None:
        raise Exception("Previous status required")

    action = {
        constants.PublisherTargetingStatus.WHITELISTED: 'Whitelisted',
        constants.PublisherTargetingStatus.BLACKLISTED: 'Blacklisted',
        constants.PublisherTargetingStatus.UNLISTED: ('Enabled' if previous_status ==
                                                      constants.PublisherTargetingStatus.BLACKLISTED else 'Disabled'),
    }[status]

    if obj is None:
        level_description = 'globally'
        history_actiontype = constants.HistoryActionType.GLOBAL_PUBLISHER_BLACKLIST_CHANGE
    else:
        level_description = 'on {} level'.format(
            constants.PublisherBlacklistLevel.get_text(obj.get_publisher_level()).lower())
        history_actiontype = constants.HistoryActionType.PUBLISHER_BLACKLIST_CHANGE

    pubs_string = u", ".join(u"{} on {}".format(
        x.publisher, x.source.name if x.source else "all sources") for x in entries)

    changes_text = u'{action} the following publishers {level_description}: {pubs}.'.format(
        action=action,
        level_description=level_description,
        pubs=pubs_string
    )

    if obj is None:
        history_helpers.write_global_history(changes_text, user=request.user, action_type=history_actiontype)
    else:
        obj.write_history(changes_text, user=request.user, action_type=history_actiontype)
        email_helper.send_obj_changes_notification_email(obj, request, changes_text)


def ping_k1(obj):
    # ping if need be
    pass


def _prepare_entries(entry_dicts, publisher_group):
    """
    Creates publisher group entries from entry dicts. Does __not__ save them to the database.
    """

    entries = []
    added = set()

    # remove duplicates
    for entry in entry_dicts:
        key = frozenset(entry.values())
        if key in added:
            continue

        added.add(key)

        entries.append(models.PublisherGroupEntry(
            publisher=entry['publisher'],
            source=entry['source'],
            include_subdomains=entry['include_subdomains'],
            outbrain_publisher_id=entry.get('outbrain_publisher_id', ''),
            outbrain_section_id=entry.get('outbrain_section_id', ''),
            outbrain_amplify_publisher_id=entry.get('outbrain_amplify_publisher_id', ''),
            outbrain_engage_publisher_id=entry.get('outbrain_engage_publisher_id', ''),
            publisher_group=publisher_group,
        ))
    return entries


def validate_blacklist_entry(obj, entry):
    if (entry.source and entry.source.source_type.type == constants.SourceType.OUTBRAIN and
            ((obj and obj.get_publisher_level() != constants.PublisherBlacklistLevel.ACCOUNT) or not obj)):
        raise PublisherGroupTargetingException("Outbrain specific blacklisting is only available on account level")


def apply_outbrain_account_constraints_if_needed(obj, enforce_cpc):
    outbrain = models.Source.objects.filter(source_type__type=constants.SourceType.OUTBRAIN)
    if not outbrain.exists():
        # some tests do not need to test outbrain and as such do not include it in fixtures
        return

    if obj is None:
        # no need to handle when we do global blacklisting:
        return

    outbrain = outbrain.first()
    account = obj.get_account()

    blacklist_ids = _get_blacklists(account, account.get_current_settings())
    entries = models.PublisherGroupEntry.objects.filter(publisher_group_id__in=blacklist_ids, source=outbrain)

    if entries.count() >= OUTBRAIN_CPC_CONSTRAINT_LIMIT:
        cpc_constraints.create(
            min_cpc=OUTBRAIN_CPC_CONSTRAINT_MIN,
            constraint_type=constants.CpcConstraintType.OUTBRAIN_BLACKLIST,
            enforce_cpc_settings=enforce_cpc,
            source=outbrain,
            account=account)
    else:
        cpc_constraints.clear(
            min_cpc=OUTBRAIN_CPC_CONSTRAINT_MIN,
            constraint_type=constants.CpcConstraintType.OUTBRAIN_BLACKLIST,
            source=outbrain,
            account=account)


def get_ob_blacklisted_publishers_count(account):
    blacklists = _get_blacklists(account, account.get_current_settings())
    return models.PublisherGroupEntry.objects.filter(publisher_group_id__in=blacklists,
                                                     source__source_type__type=constants.SourceType.OUTBRAIN).count()


def parse_default_publisher_group_origin(publisher_group):
    type_, level, obj, name = None, None, None, ""
    possible_ids = re.findall("([0-9]+)", publisher_group.name)

    if publisher_group.name.startswith("Default blacklist for account"):
        type_, level = 'Blacklist', 'Account'
        obj = models.Account.objects.filter(pk=possible_ids[-1])
    elif publisher_group.name.startswith("Default whitelist for account"):
        type_, level = 'Whitelist', 'Account'
        obj = models.Account.objects.filter(pk=possible_ids[-1])
    elif publisher_group.name.startswith("Default blacklist for campaign"):
        type_, level = 'Blacklist', 'Campaign'
        obj = models.Campaign.objects.filter(pk=possible_ids[-1])
    elif publisher_group.name.startswith("Default whitelist for campaign"):
        type_, level = 'Whitelist', 'Campaign'
        obj = models.Campaign.objects.filter(pk=possible_ids[-1])
    elif publisher_group.name.startswith("Default blacklist for ad group"):
        type_, level = 'Blacklist', 'Ad Group'
        obj = models.AdGroup.objects.filter(pk=possible_ids[-1])
    elif publisher_group.name.startswith("Default whitelist for ad group"):
        type_, level = 'Whitelist', 'Ad Group'
        obj = models.AdGroup.objects.filter(pk=possible_ids[-1])

    if obj is not None and obj.exists():
        obj = obj.first()
        name = u"{} [{}]".format(obj.name, obj.id)

    return type_, level, obj, name
