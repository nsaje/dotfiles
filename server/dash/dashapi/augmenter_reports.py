from dash import constants
from dash import publisher_helpers

from .augmenter import copy_fields_if_exists


def get_augmenter_for_dimension(target_dimension):
    if target_dimension == 'account_id':
        return augment_accounts
    elif target_dimension == 'campaign_id':
        return augment_campaigns
    elif target_dimension == 'ad_group_id':
        return augment_ad_groups
    elif target_dimension == 'content_ad_id':
        return augment_content_ads
    elif target_dimension == 'source_id':
        return augment_sources
    elif target_dimension == 'publisher_id':
        return augment_publishers


def augment_accounts(rows, loader, is_base_level=False):
    for row in rows:
        account_id = row['account_id']
        augment_row_account(
            row,
            loader.objs_map[account_id],
            loader.settings_map[account_id],
            loader.projections_map[account_id]
        )


def augment_campaigns(rows, loader, is_base_level=False):
    for row in rows:
        campaign_id = row['campaign_id']
        augment_row_campaign(
            row,
            loader.objs_map[campaign_id],
            loader.settings_map[campaign_id],
            loader.projections_map[campaign_id]
        )


def augment_ad_groups(rows, loader, is_base_level=False):
    for row in rows:
        ad_group_id = row['ad_group_id']
        augment_row_ad_group(
            row,
            loader.objs_map[ad_group_id],
            loader.settings_map[ad_group_id],
            loader.base_level_settings_map[ad_group_id] if is_base_level else None
        )


def augment_content_ads(rows, loader, is_base_level=False):
    for row in rows:
        content_ad_id = row['content_ad_id']
        augment_row_content_ad(
            row,
            loader.objs_map[content_ad_id],
            loader.batch_map[content_ad_id],
            loader.ad_group_map[content_ad_id],
            loader.per_source_status_map[content_ad_id]
        )


def augment_sources(rows, loader, is_base_level=False):
    for row in rows:
        source_id = row['source_id']
        augment_row_source(
            row,
            loader.objs_map[source_id],
            loader.settings_map[source_id]
        )


def augment_publishers(rows, loader, is_base_level=False):
    for row in rows:
        domain, _ = publisher_helpers.dissect_publisher_id(row['publisher_id'])
        source_id = row['source_id']
        augment_row_publisher(
            row,
            domain,
            loader.source_map[source_id],
            loader.blacklist_status_map[row['publisher_id']],
            loader.can_blacklist_source_map[source_id]
        )


def augment_row_account(row, account=None, settings=None, projections=None):
    if account:
        row.update({
            'account': account.name,
            'agency': account.agency.name if account.agency else '',
            'agency_id': account.agency.id if account.agency else '',
        })

    if settings:
        copy_fields_if_exists(
            ['status', 'archived', 'default_account_manager',
             'default_sales_representative', 'default_cs_representative',
             'account_type', 'salesforce_url'],
            settings, row)

    if projections is not None:
        row.update({
            'pacing': projections.get('pacing'),
            'allocated_budgets': projections.get('allocated_media_budget'),
            'spend_projection': projections.get('media_spend_projection'),
            'license_fee_projection': projections.get('license_fee_projection'),
            'flat_fee': projections.get('flat_fee'),
            'total_fee': projections.get('total_fee'),
            'total_fee_projection': projections.get('total_fee_projection'),
        })


def augment_row_campaign(row, campaign=None, settings=None, projections=None):
    if campaign:
        row.update({
            'campaign': campaign.name
        })

    if settings:
        copy_fields_if_exists(['status', 'archived', 'campaign_manager'], settings, row)

    if projections is not None:
        row.update({
            'pacing': projections.get('pacing'),
            'allocated_budgets': projections.get('allocated_media_budget'),
            'spend_projection': projections.get('media_spend_projection'),
            'license_fee_projection': projections.get('license_fee_projection'),
        })


def augment_row_ad_group(row, ad_group=None, settings=None, base_level_settings=None):
    if ad_group:
        row.update({
            'ad_group': ad_group.name,
        })

    if settings:
        copy_fields_if_exists(['archived', 'status', 'state'], settings, row)

    if base_level_settings:
        copy_fields_if_exists(['campaign_stop_inactive', 'campaign_has_available_budget'], base_level_settings, row)


def augment_row_content_ad(row, content_ad=None, batch=None, ad_group=None, status_per_source=None):
    if content_ad:
        row.update({
            'content_ad': content_ad.title,
            'display_url': content_ad.display_url,
            'brand_name': content_ad.brand_name,
            'description': content_ad.description,
            'call_to_action': content_ad.call_to_action,
            'label': content_ad.label,
            'image_url': content_ad.get_image_url(),
            'image_hash': content_ad.image_hash,
            'state': content_ad.state,
            'status': content_ad.state,
            'archived': content_ad.archived,
            'redirector_url': content_ad.get_redirector_url()
        })

        if ad_group:
            row.update({
                'url': content_ad.get_url(ad_group),
            })

    if batch:
        row.update({
            'batch_id': batch.id,
            'batch_name': batch.name,
            'upload_time': batch.created_dt,
        })

    if status_per_source:
        row['status_per_source'] = status_per_source


def augment_row_source(row, source=None, settings=None):
    if source:
        row.update({
            'source_id': source.id,
            'source': source.name,
            'source_slug': source.bidder_slug,
            'archived': source.deprecated,
            'maintenance': source.maintenance,
        })

    if settings is not None:
        copy_fields_if_exists([
            'status', 'daily_budget', 'min_bid_cpc', 'max_bid_cpc', 'state',
            'supply_dash_url', 'supply_dash_disabled_message', 'editable_fields',
            'notifications',
        ], settings, row)

        if 'bid_cpc' in settings:
            row.update({
                'bid_cpc': settings['bid_cpc'],
                'current_bid_cpc': settings['bid_cpc'],
                'current_daily_budget': settings['daily_budget'],
            })


def augment_row_publisher(row, domain, source, entry_status, can_blacklist_source):
    row.update({
        'publisher': domain,
        'source_id': source.id,
        'source': source.name,
        'source_slug': source.bidder_slug,
        'exchange': source.name,
        'domain_link': publisher_helpers.get_publisher_domain_link(domain),
        'can_blacklist_publisher': can_blacklist_source,
        'status': constants.PublisherTargetingStatus.get_text(entry_status['status']).upper(),
        'blacklisted': constants.PublisherTargetingStatus.get_text(entry_status['status']),
    })

    if entry_status.get('blacklisted_level'):
        row.update({
            'blacklisted_level': (constants.PublisherBlacklistLevel.get_text(
                entry_status.get('blacklisted_level', '')) or '').upper(),
            'blacklisted_level_description': constants.PublisherBlacklistLevel.verbose(
                entry_status['blacklisted_level'], entry_status['status']),
            'notifications': {
                'message': constants.PublisherBlacklistLevel.verbose(
                    entry_status['blacklisted_level'], entry_status['status']),
            },
        })
