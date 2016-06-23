import logging

from django.db import transaction

import dash.constants
import dash.models
import utils.k1_helper
import actionlog.models

ALLOWED_LEVEL_CONSTRAINTS = (
    'ad_group',
    'campaign',
    'account',
)

UNSUPPORTED_SOURCES = (
    dash.constants.SourceType.GRAVITY,
    dash.constants.SourceType.OUTBRAIN,
)

NOT_ENABLED_BLACKLIST_STATUSES = (
    dash.constants.PublisherStatus.BLACKLISTED,
    dash.constants.PublisherStatus.PENDING
)

logger = logging.getLogger(__name__)


def update(ad_group, constraints, status, domains, everywhere=False,
           all_sources=False, request=None):
    if everywhere:
        _global_blacklist(constraints, status, domains)
        return

    if not constraints or len(set(ALLOWED_LEVEL_CONSTRAINTS) & set(constraints.keys())) != 1:
        raise Exception('You must use exactly one of the following_constraints: {}'.format(
            ', '.join(ALLOWED_LEVEL_CONSTRAINTS)
        ))
    with transaction.atomic():
        if all_sources:
            for source in _get_sources(constraints['ad_group']):
                source_constraints = {'source': source}
                source_constraints.update(constraints)
                _update_source(source_constraints, status, domains,
                               request=request, ad_group=ad_group)
        else:
            _update_source(constraints, status, domains, request=request, ad_group=ad_group)

    if 'ad_group' in constraints:
        utils.k1_helper.update_blacklist(
            constraints['ad_group'].pk,
            msg='blacklist.update'
        )


def _get_sources(ad_group):
    ad_group_sources = dash.models.AdGroupSource.objects.filter(ad_group=ad_group)
    return set([
        ad_group_source.source
        for ad_group_source in ad_group_sources
        if ad_group_source.source.source_type.type not in UNSUPPORTED_SOURCES
    ])


def _update_source(constraints, status, domains, request=None, ad_group=None):
    source = constraints['source']

    if not source.can_modify_publisher_blacklist_automatically():
        return
    if not _handle_outbrain(source, constraints, status, domains, request, ad_group):
        return

    if status == dash.constants.PublisherStatus.ENABLED:
        globally_blacklisted = _get_globally_blacklisted_publishers_list()

        dash.models.PublisherBlacklist.objects.filter(
            everywhere=False,
            name__in=domains,
            **constraints
        ).exclude(name__in=globally_blacklisted).delete()
        return
    for domain in domains:
        dash.models.PublisherBlacklist.objects.create(
            name=domain,
            everywhere=False,
            status=status,
            **constraints
        )


def _get_globally_blacklisted_publishers_list(**constraints):
    return dash.models.PublisherBlacklist.objects.filter(
        everywhere=True,
        status=dash.constants.PublisherStatus.BLACKLISTED,
        **constraints
    ).values_list('name', flat=True)


@transaction.atomic
def _global_blacklist(constraints, status, domains):
    if set(ALLOWED_LEVEL_CONSTRAINTS) & set(constraints.keys()):
        raise Exception('On global blacklist, any non-source constraints are forbidden')

    if status == dash.constants.PublisherStatus.ENABLED:
        dash.models.PublisherBlacklist.objects.filter(
            everywhere=True,
            name__in=domains,
            **constraints
        ).delete()
        return

    domains_to_blacklist = set(domains) \
        - set(_get_globally_blacklisted_publishers_list(**constraints))\
        - set(_get_globally_blacklisted_publishers_list(source=None))

    for domain in domains_to_blacklist:
        dash.models.PublisherBlacklist.objects.create(
            name=domain,
            everywhere=True,
            status=status,
            **constraints
        )
    return True


def _handle_outbrain(source, constraints, status, domains, request, ad_group):
    if source.source_type.type != dash.constants.SourceType.OUTBRAIN:
        return True
    if 'account' not in constraints:
        return False

    ob_domains = dash.models.PublisherBlacklist.objects.filter(
        account=constraints['account'],
        source__source_type__type=dash.constants.SourceType.OUTBRAIN,
        status__in=NOT_ENABLED_BLACKLIST_STATUSES
    )
    count_ob = ob_domains.count()
    if status in NOT_ENABLED_BLACKLIST_STATUSES:
        count_ob += len(domains)
    else:
        count_ob -= len(
            set(domains) & set(ob_domains.values_list('name', flat=True))
        )

    if count_ob > dash.constants.MAX_OUTBRAIN_BLACKLISTED_PUBLISHERS_PER_ACCOUNT:
        logger.error('Attempted to blacklist more than 30 publishers per account on Outbrain')
        return False

    if count_ob > dash.constants.MANUAL_ACTION_OUTBRAIN_BLACKLIST_THRESHOLD:
        _trigger_manual_ob_blacklist_action(request, ad_group, status, domains)

    return True


def _trigger_manual_ob_blacklist_action(request, ad_group, state, domains):
    action_name = {
        dash.constants.PublisherStatus.BLACKLISTED: 'Blacklist',
        dash.constants.PublisherStatus.ENABLED: 'Enable',
    }[state]
    domains = ', '.join(domain for domain in domains)

    action = actionlog.models.ActionLog(
        action=actionlog.constants.Action.SET_PUBLISHER_BLACKLIST,
        action_type=actionlog.constants.ActionType.MANUAL,
        expiration_dt=None,
        state=actionlog.constants.ActionState.WAITING,
        ad_group_source=dash.models.AdGroupSource.objects.filter(
            ad_group=ad_group,
            source__tracking_slug=dash.constants.SourceType.OUTBRAIN
        ).first(),
        payload={
            'ad_group_id': ad_group.pk,
            'state': state,
            'domains': domains
        },
        message=u'{} the following publishers on Outbrain for account {} (#{}): {}'.format(
            action_name, ad_group.campaign.account.name, ad_group.campaign.account.pk, domains
        )
    )
    action.save(request)
