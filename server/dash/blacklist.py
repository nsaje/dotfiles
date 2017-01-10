import logging

from django.db import transaction

import dash.constants
import dash.models
import utils.k1_helper

ALLOWED_LEVEL_CONSTRAINTS = (
    'ad_group',
    'campaign',
    'account',
)

NOT_ENABLED_BLACKLIST_STATUSES = (
    dash.constants.PublisherStatus.BLACKLISTED,
    dash.constants.PublisherStatus.PENDING
)

ACTION_TO_MESSAGE = {
    dash.constants.PublisherStatus.BLACKLISTED: 'Blacklist',
    dash.constants.PublisherStatus.ENABLED: 'Enable',
}

logger = logging.getLogger(__name__)


class BlacklistException(Exception):
    pass


def update(ad_group, constraints, status, domains, everywhere=False,
           all_sources=False, all_b1_sources=False, request=None):
    external_map = dict(domains)
    domain_names = external_map.keys()
    if everywhere:
        _global_blacklist(constraints, status, domain_names, external_map)
        return

    if not constraints or len(set(ALLOWED_LEVEL_CONSTRAINTS) & set(constraints.keys())) != 1:
        raise Exception('You must use exactly one of the following_constraints: {}'.format(
            ', '.join(ALLOWED_LEVEL_CONSTRAINTS)
        ))
    with transaction.atomic():
        if all_b1_sources:
            constraints['source'] = None
            _handle_all(constraints, status, domain_names, external_map, ad_group=ad_group)
        elif all_sources:
            for source in _get_sources(constraints['ad_group']):
                source_constraints = {'source': source}
                source_constraints.update(constraints)
                _update_source(source_constraints, status, domain_names, external_map,
                               request=request, ad_group=ad_group)
        else:
            _update_source(constraints, status, domain_names, external_map,
                           request=request, ad_group=ad_group)

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
        if ad_group_source.source.can_modify_publisher_blacklist_automatically()
    ])


def _handle_all(constraints, status, domain_names, external_map, request=None,
                ad_group=None):
    if status == dash.constants.PublisherStatus.ENABLED:
        globally_blacklisted = _get_globally_blacklisted_publishers_list()
        dash.models.PublisherBlacklist.objects.filter(
            everywhere=False,
            name__in=domain_names,
            **constraints
        ).exclude(name__in=globally_blacklisted).delete()
        return

    already_blacklisted = set(dash.models.PublisherBlacklist.objects.filter(
        everywhere=False,
        name__in=domain_names,
        **constraints
    ).values_list('name', flat=True))
    for domain in set(domain_names) - already_blacklisted:
        dash.models.PublisherBlacklist.objects.create(
            name=domain,
            everywhere=False,
            status=status,
            external_id=external_map.get(domain),
            **constraints
        )


def _update_source(constraints, status, domain_names, external_map, request=None, ad_group=None):
    source = constraints['source']

    if not source.can_modify_publisher_blacklist_automatically():
        return

    if source.source_type.type == dash.constants.SourceType.OUTBRAIN and 'account' not in constraints:
        return

    _handle_all(constraints, status, domain_names, external_map, request=request, ad_group=ad_group)


def _get_globally_blacklisted_publishers_list(**constraints):
    return dash.models.PublisherBlacklist.objects.filter(
        everywhere=True,
        status=dash.constants.PublisherStatus.BLACKLISTED,
        **constraints
    ).values_list('name', flat=True)


@transaction.atomic
def _global_blacklist(constraints, status, domain_names, external_map):
    if set(ALLOWED_LEVEL_CONSTRAINTS) & set(constraints.keys()):
        raise Exception('On global blacklist, any non-source constraints are forbidden')

    if status == dash.constants.PublisherStatus.ENABLED:
        dash.models.PublisherBlacklist.objects.filter(
            everywhere=True,
            name__in=domain_names,
            **constraints
        ).delete()
        return

    domains_to_blacklist = set(domain_names) \
        - set(_get_globally_blacklisted_publishers_list(**constraints))\
        - set(_get_globally_blacklisted_publishers_list(source=None))

    for domain in domains_to_blacklist:
        dash.models.PublisherBlacklist.objects.create(
            name=domain,
            everywhere=True,
            status=status,
            external_id=external_map.get(domain),
            **constraints
        )


def _handle_outbrain(source, constraints, status, domain_names, external_map, request, ad_group):
    if 'account' not in constraints:
        raise BlacklistException('OB blacklist is allowed only on account level')
