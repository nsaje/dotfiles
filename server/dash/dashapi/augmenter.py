from dash.views import helpers as view_helpers
from dash import constants

"""
Applies dash data to rows. No logics, only write data to proper keys.
"""


def augment_accounts(rows, loader, is_base_level=False):
    for row in rows:
        account_id = row['account_id']
        augment_row_account(
            row,
            loader.objs_map[account_id],
            loader.settings_map[account_id],
            loader.status_map[account_id],
            loader.projections_map[account_id]
        )


def augment_accounts_totals(row, loader):
    augment_row_account(row, projections=loader.projections_totals)


def augment_campaigns(rows, loader, is_base_level=False):
    for row in rows:
        campaign_id = row['campaign_id']
        augment_row_campaign(
            row,
            loader.objs_map[campaign_id],
            loader.settings_map[campaign_id],
            loader.status_map[campaign_id],
            loader.projections_map[campaign_id]
        )


def augment_campaigns_totals(row, loader):
    augment_row_campaign(row, projections=loader.projections_totals)


def augment_ad_groups(rows, loader, is_base_level=False):
    for row in rows:
        ad_group_id = row['ad_group_id']
        augment_row_ad_group(
            row,
            loader.objs_map[ad_group_id],
            loader.settings_map[ad_group_id],
            loader.status_map[ad_group_id],
            loader.other_settings_map[ad_group_id] if is_base_level else None
        )


def augment_content_ads(rows, loader, is_base_level=False):
    for row in rows:
        content_ad_id = row['content_ad_id']
        augment_row_content_ad(
            row,
            loader.objs_map[content_ad_id],
            loader.batch_map[content_ad_id],
            loader.ad_group_map[content_ad_id],
            loader.is_demo_map[content_ad_id]
        )


def augment_sources(rows, loader, is_base_level=False):
    for row in rows:
        source_id = row['source_id']
        augment_row_source(
            row,
            loader.objs_map[source_id],
            loader.settings_map[source_id]
        )


def augment_sources_totals(row, loader):
    augment_row_source(row, settings=loader.totals)


def augment_row_account(row, account=None, settings=None, status=None, projections=None):
    if account:
        row.update({
            'name': account.name,
            'agency': account.agency.name if account.agency else '',
        })

    if settings:
        row.update({
            'archived': settings.archived,
            'default_account_manager': view_helpers.get_user_full_name_or_email(
                settings.default_account_manager, default_value=None),
            'default_sales_representative': view_helpers.get_user_full_name_or_email(
                settings.default_sales_representative, default_value=None),
            'account_type': constants.AccountType.get_text(settings.account_type),
        })

    if status is not None:
        row.update({
            'status': status,
        })

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


def augment_row_campaign(row, campaign=None, settings=None, status=None, projections=None):
    if campaign:
        row.update({
            'name': campaign.name
        })

    if settings:
        row.update({
            'archived': settings.archived,
            'campaign_manager': view_helpers.get_user_full_name_or_email(
                settings.campaign_manager, default_value=None),
        })

    if status is not None:
        row.update({
            'status': status,
        })

    if projections is not None:
        row.update({
            'pacing': projections.get('pacing'),
            'allocated_budgets': projections.get('allocated_media_budget'),
            'spend_projection': projections.get('media_spend_projection'),
            'license_fee_projection': projections.get('license_fee_projection'),
        })


def augment_row_ad_group(row, ad_group=None, settings=None, status=None, other_settings=None):
    if ad_group:
        row.update({
            'name': ad_group.name,
        })

    if settings:
        row.update({
            'archived': settings.archived,
        })

    if status is not None:
        row.update({
            'status': status,
            'state': status,
        })

    if other_settings is not None:
        row.update(other_settings)


def augment_row_content_ad(row, content_ad=None, batch=None, ad_group=None, is_demo=None):
    if content_ad:
        row.update({
            'name': content_ad.title,
            'title': content_ad.title,
            'display_url': content_ad.display_url,
            'brand_name': content_ad.brand_name,
            'description': content_ad.description,
            'call_to_action': content_ad.call_to_action,
            'label': content_ad.label,
            'image_urls': {
                'square': content_ad.get_image_url(160, 160),
                'landscape': content_ad.get_image_url(256, 160)
            },
            'image_hash': content_ad.image_hash,
            'state': content_ad.state,
            'status': content_ad.state,
            'archived': content_ad.archived,
            'redirector_url': content_ad.get_redirector_url(is_demo)
        })

        if ad_group:
            row.update({
                'url': content_ad.get_url(ad_group, is_demo),
            })

    if batch:
        row.update({
            'batch_id': batch.id,
            'batch_name': batch.name,
            'upload_time': batch.created_dt,
        })


def augment_row_source(row, source=None, settings=None):
    if source:
        row.update({
            'name': source.name,
            'archived': source.deprecated,
            'maintenance': source.maintenance,
        })

    if settings is not None:
        row.update(settings)
