from utils.sort_helper import dissect_order
from dash import table

from dash.dashapi import loaders
from dash.dashapi import augmenter
from dash.dashapi.helpers import apply_offset_limit


def query_accounts(accounts_qs, filtered_sources_qs, show_archived, order, offset, limit):
    _, order_field = dissect_order(order)

    if order_field == 'name':
        rows, loader = _query_general_ordered_by_name(accounts_qs, filtered_sources_qs, show_archived,
                                                      order, offset, limit,
                                                      loaders.AccountsLoader, 'account_id', augmenter.augment_row_account)
    elif order_field == 'status':
        rows, loader = _query_general_ordered_by_status(accounts_qs, filtered_sources_qs, show_archived,
                                                        order, offset, limit,
                                                        loaders.AccountsLoader, 'account_id', augmenter.augment_row_account)
    else:
        raise Exception("This order field name is not supported")

    augmenter.augment_accounts(rows, loader)

    return rows


def query_campaigns(campaigns_qs, filtered_sources_qs, show_archived, order, offset, limit):
    _, order_field = dissect_order(order)

    if order_field == 'name':
        rows, loader = _query_general_ordered_by_name(campaigns_qs, filtered_sources_qs, show_archived,
                                                      order, offset, limit,
                                                      loaders.CampaignsLoader, 'campaign_id', augmenter.augment_row_campaign)
    elif order_field == 'status':
        rows, loader = _query_general_ordered_by_status(campaigns_qs, filtered_sources_qs, show_archived,
                                                        order, offset, limit,
                                                        loaders.CampaignsLoader, 'campaign_id', augmenter.augment_row_campaign)
    else:
        raise Exception("This order field name is not supported")

    augmenter.augment_campaigns(rows, loader)

    return rows


def query_ad_groups(ad_groups_qs, filtered_sources_qs, show_archived, order, offset, limit):
    _, order_field = dissect_order(order)
    if order_field == 'name':
        rows, loader = _query_general_ordered_by_name(ad_groups_qs, filtered_sources_qs, show_archived,
                                                      order, offset, limit,
                                                      loaders.AdGroupsLoader, 'ad_group_id', augmenter.augment_row_ad_group)
    elif order_field == 'status':
        rows, loader = _query_general_ordered_by_status(ad_groups_qs, filtered_sources_qs, show_archived,
                                                        order, offset, limit,
                                                        loaders.AdGroupsLoader, 'ad_group_id', augmenter.augment_row_ad_group)
    else:
        raise Exception("This order field name is not supported")

    augmenter.augment_ad_groups(rows, loader)

    return rows


def query_content_ads(content_ads_qs, filtered_sources_qs, show_archived, order, offset, limit):
    _, order_field = dissect_order(order)

    if order_field in ('name', 'title', 'url', 'display_url', 'brand_name', 'description', 'call_to_action',
                       'label', 'state', 'status', 'batch_name', 'upload_time'):

        rows, loader = _query_content_ads_ordered_by_anything(content_ads_qs, filtered_sources_qs, show_archived, order, offset, limit)
    else:
        raise Exception("This order field name is not supported")

    augmenter.augment_content_ads(rows, loader)

    return rows


def query_sources(sources_qs, ad_groups_sources, order, offset, limit):
    _, order_field = dissect_order(order)

    if order_field == 'name':
        rows, loader = _query_sources_ordered_by_name(sources_qs, ad_groups_sources, order, offset, limit)
    elif order_field == 'status':
        rows, loader = _query_sources_ordered_by_status(sources_qs, ad_groups_sources, order, offset, limit)
    else:
        raise Exception("This order field name is not supported")

    augmenter.augment_sources(rows, loader)

    return rows


def _query_sources_ordered_by_name(sources_qs, ad_group_sources, order, offset, limit):
    sources_qs = apply_offset_limit(sources_qs.order_by(order), offset, limit)

    loader = loaders.SourcesLoader(sources_qs, ad_group_sources)

    rows = []
    for source in loader.objs_qs:
        # TODO show archived - remove sources that are deprecated and without data
        row = {'source_id': source.id}
        augmenter.augment_row_source(row, source)
        rows.append(row)

    return rows, loader


def _query_sources_ordered_by_status(sources_qs, ad_group_sources, order, offset, limit):
    loader = loaders.SourcesLoader(sources_qs, ad_group_sources)

    rows = []
    for source_id, status in loader.status_map.iteritems():
        source = loader.objs_map[source_id]

        row = {'source_id': source_id}
        augmenter.augment_row_source(row, source, status)

        rows.append(row)

    rows = table.sort_rows_by_order_and_archived(rows, order)
    rows = apply_offset_limit(rows, offset, limit)

    return rows, loader


def _query_general_ordered_by_status(objs_qs, filtered_sources_qs, show_archived, order, offset, limit,
                                     loader_cls, obj_id_key, augment_fn):
    loader = loader_cls(objs_qs, filtered_sources_qs)
    rows = []

    for obj_id, obj in loader.objs_map.iteritems():

        settings = loader.settings_map[obj_id]
        # exclude archived
        if not show_archived and settings.archived:
            continue

        row = {obj_id_key: obj_id}
        augment_fn(row, settings=settings, status=loader.status_map[obj_id])
        rows.append(row)

    rows = table.sort_rows_by_order_and_archived(rows, order)
    rows = apply_offset_limit(rows, offset, limit)

    return rows, loader


def _query_general_ordered_by_name(objs_qs, filtered_sources_qs, show_archived, order, offset, limit,
                                   loader_cls, obj_id_key, augment_fn):

    objs_qs = objs_qs.order_by(order)

    if not show_archived:
        temp_loader = loader_cls(objs_qs, filtered_sources_qs)
        archived_ids = [
            obj_id for obj_id, settings in temp_loader.settings_map.iteritems() if settings.archived
        ]
        objs_qs = objs_qs.exclude(pk__in=archived_ids)

    objs_qs = apply_offset_limit(objs_qs, offset, limit)
    loader = loader_cls(objs_qs, filtered_sources_qs)

    rows = []
    for obj in loader.objs_qs:
        row = {obj_id_key: obj.id}
        augment_fn(row, obj)
        rows.append(row)

    return rows, loader


def _query_content_ads_ordered_by_anything(content_ads_qs, filtered_sources_qs, show_archived, order, offset, limit):
    order_prefix, order_field = dissect_order(order)

    order_to_field = {
        'name': 'title',
        'status': 'state',
        'batch_name': 'batch__name',
        'upload_time': 'batch__created_dt',
    }

    if order_field in order_to_field:
        order = order_prefix + order_to_field[order_field]

    content_ads_qs = content_ads_qs.order_by(order)

    if not show_archived:
        temp_cache = loaders.ContentAdsLoader(content_ads_qs, filtered_sources_qs)
        archived_ids = [
            content_ad_id for content_ad_id, content_ad in temp_cache.objs_map.iteritems() if content_ad.archived
        ]

        content_ads_qs = content_ads_qs.exclude(pk__in=archived_ids)

    content_ads_qs = apply_offset_limit(content_ads_qs, offset, limit)
    loader = loaders.ContentAdsLoader(content_ads_qs, filtered_sources_qs)

    rows = []
    for content_ad in loader.objs_qs:
        row = {'content_ad_id': content_ad.id}
        augmenter.augment_row_content_ad(row, content_ad=content_ad)
        rows.append(row)

    return rows, loader
