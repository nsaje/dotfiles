import core.features.bid_modifiers
import stats.constants
from core.features.bid_modifiers import create_bid_modifier_dict
from core.models.tags import helpers as tag_helpers
from dash import constants
from dash import publisher_helpers

"""
Applies dash data to rows. No logics, only write data to proper keys.
"""

# HACK hardcoded for newscorp
NEWSCORP_LIVE_PREVIEW_URL = "https://www.taste.com.au/recipes/tandoori-roast-cauliflower-rice/g9h9ol5t?_b1_ad_group_id={ad_group_id}&_b1_cpm=500&_b1_no_targeting=1"


def get_augmenter_for_dimension(target_dimension):
    if target_dimension == "account_id":
        return generate_loop_function(augment_account)
    elif target_dimension == "campaign_id":
        return generate_loop_function(augment_campaign)
    elif target_dimension == "ad_group_id":
        return generate_loop_function(augment_ad_group)
    elif target_dimension == "content_ad_id":
        return generate_loop_function(augment_content_ad, augment_content_ad_for_breakdowns)
    elif target_dimension == "source_id":
        return generate_loop_function(augment_source)
    elif target_dimension == "publisher_id":
        return generate_loop_function(augment_publisher)
    elif target_dimension == "placement_id":
        return generate_loop_function(augment_placement)
    elif stats.constants.is_top_level_delivery_dimension(target_dimension):
        return generate_loop_function(augment_delivery)


def get_report_augmenter_for_dimension(target_dimension, level):
    if target_dimension == "account_id":
        return generate_loop_function(augment_account, augment_account_for_report)
    elif target_dimension == "campaign_id":
        return generate_loop_function(augment_campaign, augment_campaign_for_report)
    elif target_dimension == "ad_group_id":
        return generate_loop_function(augment_ad_group, augment_ad_group_for_report)
    elif target_dimension == "content_ad_id":
        return generate_loop_function(augment_content_ad, augment_content_ad_for_report)
    elif target_dimension == "source_id":
        return generate_loop_function(augment_source, augment_source_for_report)
    elif target_dimension == "publisher_id":
        return generate_loop_function(augment_publisher, augment_publisher_for_report)
    elif target_dimension == "placement_id":
        return generate_loop_function(augment_placement, augment_placement_for_report)
    elif stats.constants.is_top_level_delivery_dimension(target_dimension):
        return generate_loop_function(augment_delivery, augment_delivery_for_report)


def generate_loop_function(*augment_funcs):
    def loop_function(rows, *args, **kwargs):
        for row in rows:
            for augment in augment_funcs:
                augment(row, *args, **kwargs)

    return loop_function


def augment_accounts_totals(row, loader):
    augment_account(row, loader)


def augment_campaigns_totals(row, loader):
    augment_campaign(row, loader)


def augment_sources_totals(row, loader):
    augment_source(row, loader)


def augment_account(row, loader, is_base_level=False):
    account_id = row.get("account_id")

    if account_id:
        account = loader.objs_map[account_id]
        row.update(
            {
                "name": account.name,
                "agency_id": account.agency_id,
                "agency": account.agency.name if account.agency else "",
                "sspd_url": account.get_sspd_url(),
            }
        )

        settings = loader.settings_map[account_id]
        copy_fields_if_exists(
            [
                "status",
                "archived",
                "default_account_manager",
                "default_sales_representative",
                "default_cs_representative",
                "ob_sales_representative",
                "ob_account_manager",
                "account_type",
                "salesforce_url",
            ],
            settings,
            row,
        )

        refunds = loader.refunds_map.get(account_id)

        row["daily_budget"] = loader.daily_budgets_map.get(account_id, 0)
        if loader.include_entity_tags:
            if account.agency:
                row.update(
                    {"agency_tags": tag_helpers.entity_tag_query_set_to_string(account.agency.entity_tags.all())}
                )
            else:
                row.update({"agency_tags": ""})

            row.update({"account_tags": tag_helpers.entity_tag_query_set_to_string(account.entity_tags.all())})

    else:
        row["daily_budget"] = sum([daily_budget for daily_budget in loader.daily_budgets_map.values()])
        refunds = loader.refunds_totals

    if refunds:
        row.update(refunds)


def augment_account_for_report(row, loader, is_base_level=False):
    account_id = row.get("account_id")

    if account_id:
        account = loader.objs_map[account_id]
        settings = loader.settings_map[account_id]
        row.update(
            {
                "account": account.name,
                "agency_id": account.agency.id if account.agency else "",
                "status": constants.AdGroupRunningStatus.get_text(settings["status"]).upper(),
                "account_status": constants.AdGroupRunningStatus.get_text(settings["status"]).upper(),
            }
        )


def augment_campaign(row, loader, is_base_level=False):
    campaign_id = row.get("campaign_id")

    refunds = None
    if campaign_id:
        campaign = loader.objs_map[campaign_id]
        row.update(
            {
                "agency_id": campaign.account.agency_id,
                "account_id": campaign.account_id,
                "name": campaign.name,
                "sspd_url": campaign.get_sspd_url(),
                "campaign_type": constants.CampaignType.get_text(campaign.type),
            }
        )

        settings = loader.settings_map[campaign_id]
        copy_fields_if_exists(["status", "archived", "campaign_manager"], settings, row)

        row["daily_budget"] = loader.daily_budgets_map.get(campaign_id, 0)
        if loader.include_entity_tags:
            row.update({"campaign_tags": tag_helpers.entity_tag_query_set_to_string(campaign.entity_tags.all())})

    else:
        row["daily_budget"] = sum([daily_budget for daily_budget in loader.daily_budgets_map.values()])
        refunds = loader.refunds_totals

    if refunds:
        row.update(refunds)


def augment_campaign_for_report(row, loader, is_base_level=False):
    campaign_id = row.get("campaign_id")

    if campaign_id:
        campaign = loader.objs_map[campaign_id]
        settings = loader.settings_map[campaign_id]
        row.update(
            {
                "campaign": campaign.name,
                "status": constants.AdGroupRunningStatus.get_text(settings["status"]).upper(),
                "campaign_status": constants.AdGroupRunningStatus.get_text(settings["status"]).upper(),
            }
        )


def augment_ad_group(row, loader, is_base_level=False):
    ad_group_id = row.get("ad_group_id")

    if ad_group_id:
        ad_group = loader.objs_map[ad_group_id]
        row.update(
            {
                "agency_id": ad_group.campaign.account.agency_id,
                "account_id": ad_group.campaign.account_id,
                "campaign_id": ad_group.campaign_id,
                "name": ad_group.name,
                "sspd_url": ad_group.get_sspd_url(),
            }
        )

        settings = loader.settings_map[ad_group_id]
        copy_fields_if_exists(["archived", "status", "state"], settings, row)

        if is_base_level:
            base_level_settings = loader.base_level_settings_map[ad_group_id]
            copy_fields_if_exists(["campaign_has_available_budget"], base_level_settings, row)

        if loader.include_entity_tags:
            row.update({"ad_group_tags": tag_helpers.entity_tag_query_set_to_string(ad_group.entity_tags.all())})


def augment_ad_group_for_report(row, loader, is_base_level=False):
    ad_group_id = row.get("ad_group_id")

    if ad_group_id:
        ad_group = loader.objs_map[ad_group_id]
        settings = loader.settings_map[ad_group_id]
        row.update(
            {
                "ad_group": ad_group.name,
                "status": constants.AdGroupSettingsState.get_text(settings["status"]).upper(),
                "ad_group_status": constants.AdGroupSettingsState.get_text(settings["status"]).upper(),
            }
        )


def augment_content_ad(row, loader, is_base_level=False):
    content_ad_id = row.get("content_ad_id")

    if content_ad_id:
        content_ad = loader.objs_map[content_ad_id]

        row.update(
            {
                "agency_id": content_ad.ad_group.campaign.account.agency_id,
                "account_id": content_ad.ad_group.campaign.account_id,
                "campaign_id": content_ad.ad_group.campaign_id,
                "ad_group_id": content_ad.ad_group_id,
                "name": content_ad.title,
                "title": content_ad.title,
                "creative_type": constants.AdType.get_text(content_ad.type),
                "creative_size": content_ad.get_creative_size(),
                "display_url": content_ad.display_url,
                "brand_name": content_ad.brand_name,
                "description": content_ad.description,
                "call_to_action": content_ad.call_to_action,
                "label": content_ad.label,
                "image_urls": {
                    "square": content_ad.get_image_url(300, 300),
                    "landscape": content_ad.get_image_url(720, 450),
                    "portrait": content_ad.get_image_url(375, 480),
                    "image": content_ad.get_image_url(),
                    "ad_tag": content_ad.ad_tag,
                },
                "image_hash": content_ad.image_hash,
                "tracker_urls": content_ad.tracker_urls or [],
                "state": content_ad.state,
                "status": content_ad.state,
                "archived": content_ad.archived,
                "redirector_url": content_ad.get_redirector_url(),
                "sspd_url": content_ad.get_sspd_url(),
            }
        )

        if hasattr(loader, "bid_modifiers_by_ad"):
            bid_modifier = loader.bid_modifiers_by_ad.get(content_ad_id)
            row.update(
                {
                    "bid_modifier": create_bid_modifier_dict(
                        bid_modifier,
                        modifier_type=core.features.bid_modifiers.BidModifierType.get_name(
                            core.features.bid_modifiers.BidModifierType.AD
                        ),
                        target=str(content_ad_id),
                    )
                }
            )

        ad_group = loader.ad_group_map[content_ad_id]
        row.update({"url": content_ad.get_url(ad_group)})

        batch = loader.batch_map[content_ad_id]
        row.update({"batch_id": batch.id, "batch_name": batch.name, "upload_time": batch.created_dt})

        row["image_urls"]["icon"] = content_ad.get_hosted_icon_url(300)

        if loader.user.has_perm("zemauth.can_see_amplify_live_preview"):
            row["amplify_live_preview_link"] = NEWSCORP_LIVE_PREVIEW_URL.format(ad_group_id=ad_group.id)

        amplify_internal_id = loader.amplify_internal_ids_map.get(content_ad_id)
        if loader.user.has_perm("zemauth.can_see_amplify_ad_id_column") and amplify_internal_id:
            row["amplify_promoted_link_id"] = amplify_internal_id

        row.update({"editable_fields": {"bid_modifier": {"enabled": True, "message": None}}})


def augment_content_ad_for_breakdowns(row, loader, is_base_level=False):
    content_ad_id = row.get("content_ad_id")

    if content_ad_id:
        status_per_source = loader.per_source_status_map[content_ad_id]
        row["status_per_source"] = status_per_source


def augment_content_ad_for_report(row, loader, is_base_level=False):
    content_ad_id = row.get("content_ad_id")

    if content_ad_id:
        content_ad = loader.objs_map[content_ad_id]
        row.update(
            {
                "content_ad": content_ad.title,
                "image_url": content_ad.get_image_url(),
                "status": constants.ContentAdSourceState.get_text(content_ad.state).upper(),
                "content_ad_status": constants.ContentAdSourceState.get_text(content_ad.state).upper(),
            }
        )

        if hasattr(loader, "bid_modifiers_by_ad"):
            bid_modifier = loader.bid_modifiers_by_ad.get(content_ad_id)
            row.update({"bid_modifier": bid_modifier.modifier if bid_modifier else None})


def augment_source(row, loader, is_base_level=False):
    source_id = row.get("source_id")

    if source_id:
        source = loader.objs_map[source_id]
        row.update(
            {
                "id": source.id,
                "name": source.name,
                "source_slug": source.bidder_slug,
                "archived": source.deprecated,
                "maintenance": source.maintenance,
            }
        )

        if loader.include_entity_tags:
            row.update({"source_tags": tag_helpers.entity_tag_query_set_to_string(source.entity_tags.all())})

        settings = loader.settings_map[source_id]
    else:
        settings = loader.totals

    if settings is not None:
        copy_fields_if_exists(
            [
                "status",
                "daily_budget",
                "local_daily_budget",
                "min_bid_cpc",
                "max_bid_cpc",
                "min_bid_cpm",
                "max_bid_cpm",
                "state",
                "supply_dash_url",
                "supply_dash_disabled_message",
                "editable_fields",
                "notifications",
            ],
            settings,
            row,
        )

        if "bid_cpc" in settings:
            row.update(
                {
                    "bid_cpc": settings["bid_cpc"],
                    "local_bid_cpc": settings["local_bid_cpc"],
                    "current_bid_cpc": settings["bid_cpc"],
                    "local_current_bid_cpc": settings["local_bid_cpc"],
                }
            )

        if "bid_cpm" in settings:
            row.update(
                {
                    "bid_cpm": settings["bid_cpm"],
                    "local_bid_cpm": settings["local_bid_cpm"],
                    "current_bid_cpm": settings["bid_cpm"],
                    "local_current_bid_cpm": settings["local_bid_cpm"],
                }
            )

        if "bid_cpc" in settings or "bid_cpm" in settings:
            row.update(
                {
                    "current_daily_budget": settings["daily_budget"],
                    "local_current_daily_budget": settings["local_daily_budget"],
                }
            )

    if hasattr(loader, "bid_modifiers_by_source"):
        bid_modifier = loader.bid_modifiers_by_source.get(source_id)
        row["bid_modifier"] = create_bid_modifier_dict(
            bid_modifier,
            modifier_type=core.features.bid_modifiers.BidModifierType.get_name(
                core.features.bid_modifiers.BidModifierType.SOURCE
            ),
            target=core.features.bid_modifiers.ApiConverter.from_target(
                core.features.bid_modifiers.BidModifierType.SOURCE, source_id
            )
            if source_id is not None
            else None,
        )


def augment_source_for_report(row, loader, is_base_level=False):
    source_id = row.get("source_id")

    if source_id:
        source = loader.objs_map[source_id]
        row.update({"source": source.name})
        status = loader.settings_map[source_id].get("status")
        if status is not None:
            row.update(
                {
                    "status": constants.AdGroupSourceSettingsState.get_text(status).upper(),
                    "source_status": constants.AdGroupSourceSettingsState.get_text(status).upper(),
                }
            )

        if hasattr(loader, "bid_modifiers_by_source"):
            bid_modifier = loader.bid_modifiers_by_source.get(source_id)
            row.update({"bid_modifier": bid_modifier.modifier if bid_modifier else None})


def augment_publisher(row, loader, is_base_level=False):
    domain, _ = publisher_helpers.dissect_publisher_id(row["publisher_id"])
    source_id = row["source_id"]
    source = loader.source_map[source_id]
    entry_status = loader.find_blacklisted_status_by_subdomain(row)

    row.update(
        {
            "name": domain,
            "source_id": source.id,
            "source_name": source.name,
            "source_slug": source.bidder_slug,
            "exchange": source.name,
            "domain": domain,
            "domain_link": publisher_helpers.get_publisher_domain_link(domain),
            "status": entry_status["status"],
            "blacklisted": constants.PublisherTargetingStatus.get_text(entry_status["status"]),
        }
    )

    if entry_status.get("blacklisted_level"):
        row.update(
            {
                "blacklisted_level": entry_status["blacklisted_level"],
                "blacklisted_level_description": constants.PublisherBlacklistLevel.verbose(
                    entry_status["blacklisted_level"], entry_status["status"]
                ),
                "notifications": {
                    "message": constants.PublisherBlacklistLevel.verbose(
                        entry_status["blacklisted_level"], entry_status["status"]
                    )
                },
            }
        )

    if loader.has_bid_modifiers:
        modifier_map = loader.modifier_map
        modifier = modifier_map.get((source_id, domain))

        if modifier is not None:
            row.update(
                {
                    "bid_modifier": create_bid_modifier_dict(
                        modifier,
                        modifier_type=core.features.bid_modifiers.BidModifierType.get_name(modifier.type),
                        target=core.features.bid_modifiers.ApiConverter.from_target(modifier.type, modifier.target),
                        source_slug=modifier.source_slug,
                    )
                }
            )
        else:
            row.update(
                {
                    "bid_modifier": create_bid_modifier_dict(
                        None,
                        modifier_type=core.features.bid_modifiers.BidModifierType.get_name(
                            core.features.bid_modifiers.BidModifierType.PUBLISHER
                        ),
                        target=core.features.bid_modifiers.ApiConverter.from_target(
                            core.features.bid_modifiers.BidModifierType.PUBLISHER, domain
                        ),
                        source_slug=source.bidder_slug,
                    )
                }
            )

        editable = True
        message = None
        if source.source_type.type in [constants.SourceType.YAHOO, constants.SourceType.OUTBRAIN]:
            editable = False
            message = "This source does not support bid modifiers."
        row.update({"editable_fields": {"bid_modifier": {"enabled": editable, "message": message}}})


def augment_publisher_for_report(row, loader, is_base_level=False):
    domain, _ = publisher_helpers.dissect_publisher_id(row["publisher_id"])
    source_id = row["source_id"]
    source = loader.source_map[source_id]
    entry_status = loader.find_blacklisted_status_by_subdomain(row)

    row.update(
        {
            "publisher": domain,
            "source": source.name,
            "status": constants.PublisherTargetingStatus.get_text(entry_status["status"]).upper(),
            "publisher_status": constants.PublisherTargetingStatus.get_text(entry_status["status"]).upper(),
            "blacklisted_level": (
                constants.PublisherBlacklistLevel.get_text(entry_status.get("blacklisted_level", "")) or ""
            ).upper(),
        }
    )

    if loader.has_bid_modifiers:
        modifier_map = loader.modifier_map
        modifier = modifier_map.get((source_id, domain))
        row.update({"bid_modifier": modifier.modifier if modifier else None})


def augment_placement(row, loader, is_base_level=False):
    domain, _, _ = publisher_helpers.dissect_placement_id(row["placement_id"])
    source_id = row["source_id"]
    source = loader.source_map[source_id]
    entry_status = loader.find_blacklisted_status_by_subdomain(row)

    row.update(
        {
            "name": row["placement"] or stats.constants.NOT_REPORTED,
            "source_id": source.id,
            "source_name": source.name,
            "source_slug": source.bidder_slug,
            "exchange": source.name,
            "domain": domain,
            "domain_link": publisher_helpers.get_publisher_domain_link(domain),
            "status": entry_status["status"],
            "blacklisted": constants.PublisherTargetingStatus.get_text(entry_status["status"]),
        }
    )

    if entry_status.get("blacklisted_level"):
        row.update(
            {
                "blacklisted_level": entry_status["blacklisted_level"],
                "blacklisted_level_description": constants.PublisherBlacklistLevel.verbose(
                    entry_status["blacklisted_level"], entry_status["status"]
                ),
                "notifications": {
                    "message": constants.PublisherBlacklistLevel.verbose(
                        entry_status["blacklisted_level"], entry_status["status"]
                    )
                },
            }
        )

    if loader.has_bid_modifiers:
        modifier = loader.modifier_map.get(row["placement_id"])

        editable = True
        message = None

        if modifier is not None:
            row.update(
                {
                    "bid_modifier": create_bid_modifier_dict(
                        modifier,
                        modifier_type=core.features.bid_modifiers.BidModifierType.get_name(modifier.type),
                        target=core.features.bid_modifiers.ApiConverter.from_target(modifier.type, modifier.target),
                        source_slug=modifier.source_slug,
                    )
                }
            )
        elif not row["placement"]:
            editable = False
            message = "Bid modifier can not be applied if placement is not reported"
            row.update({"bid_modifier": None})
        else:
            row.update(
                {
                    "bid_modifier": create_bid_modifier_dict(
                        None,
                        modifier_type=core.features.bid_modifiers.BidModifierType.get_name(
                            core.features.bid_modifiers.BidModifierType.PLACEMENT
                        ),
                        target=core.features.bid_modifiers.ApiConverter.from_target(
                            core.features.bid_modifiers.BidModifierType.PLACEMENT, row["placement_id"]
                        ),
                        source_slug=source.bidder_slug,
                    )
                }
            )

        if source.source_type.type in [constants.SourceType.YAHOO, constants.SourceType.OUTBRAIN]:
            editable = False
            message = "This source does not support bid modifiers."

        row.update({"editable_fields": {"bid_modifier": {"enabled": editable, "message": message}}})


def augment_placement_for_report(row, loader, is_base_level=False):
    source_id = row["source_id"]
    source = loader.source_map[source_id]
    entry_status = loader.find_blacklisted_status_by_subdomain(row)

    row.update(
        {
            "source": source.name,
            "status": constants.PublisherTargetingStatus.get_text(entry_status["status"]).upper(),
            "publisher_status": constants.PublisherTargetingStatus.get_text(entry_status["status"]).upper(),
            "blacklisted_level": (
                constants.PublisherBlacklistLevel.get_text(entry_status.get("blacklisted_level", "")) or ""
            ).upper(),
        }
    )

    if loader.has_bid_modifiers:
        modifier = loader.modifier_map.get(row["placement_id"])
        row.update({"bid_modifier": modifier.modifier if modifier else None})


def augment_delivery(row, loader, is_base_level=True):
    if not loader.ad_group:
        return

    delivery_dimension = loader.delivery_dimension
    delivery_value = row.get(loader.delivery_dimension)

    if delivery_value not in core.features.bid_modifiers.constants.UNSUPPORTED_TARGETS:
        bid_modifier = loader.objs_map.get(delivery_value)
        row.update(
            {
                "bid_modifier": create_bid_modifier_dict(
                    bid_modifier,
                    modifier_type=core.features.bid_modifiers.BidModifierType.get_name(
                        core.features.bid_modifiers.helpers.breakdown_name_to_modifier_type(delivery_dimension)
                    ),
                    target=core.features.bid_modifiers.ApiConverter.from_target(
                        core.features.bid_modifiers.helpers.breakdown_name_to_modifier_type(delivery_dimension),
                        delivery_value,
                    ),
                )
            }
        )

    row.update({"editable_fields": {"bid_modifier": {"enabled": True, "message": None}}})


def augment_delivery_for_report(row, loader, is_base_level=True):
    if not loader.ad_group:
        return

    delivery_value = row.get(loader.delivery_dimension)
    bid_modifier = loader.objs_map.get(delivery_value)

    row.update({"bid_modifier": bid_modifier.modifier if bid_modifier else None})


def augment_parent_ids(rows, loader_map, dimension):
    parent_dimensions = {"content_ad_id": "ad_group_id", "ad_group_id": "campaign_id", "campaign_id": "account_id"}
    parent_dimension = parent_dimensions.get(dimension)
    if parent_dimension is None:
        return

    loader = loader_map.get(dimension)
    if loader is None:
        return

    for row in rows:
        row[parent_dimension] = getattr(loader.objs_map[row[dimension]], parent_dimension)

    augment_parent_ids(rows, loader_map, parent_dimension)


def make_dash_rows(target_dimension, loader, parent):
    if target_dimension == "publisher_id":
        return make_publisher_dash_rows(loader.objs_ids)
    if target_dimension == "placement_id":
        return make_placement_dash_rows(loader.objs_ids)
    if stats.constants.is_top_level_delivery_dimension(target_dimension):
        return make_delivery_dash_rows(target_dimension, loader.objs_map)
    return [make_row(target_dimension, obj_id, parent) for obj_id in loader.objs_ids]


def make_publisher_dash_rows(objs_ids):
    rows = []
    for obj_id in objs_ids:
        publisher, source_id = publisher_helpers.dissect_publisher_id(obj_id)

        # dont include rows without source_id
        if source_id:
            rows.append({"publisher_id": obj_id, "publisher": publisher, "source_id": source_id})

    return rows


def make_placement_dash_rows(objs_ids):
    rows = []
    for obj_id in objs_ids:
        publisher, source_id, placement = publisher_helpers.dissect_placement_id(obj_id)
        publisher_id = publisher_helpers.create_publisher_id(publisher, source_id)

        # dont include rows without source_id or placement
        if all((source_id, placement)):
            rows.append(make_placement_dash_row(publisher_id, publisher, placement, source_id))

    return rows


def make_placement_dash_row(publisher_id, publisher, placement, source_id):
    placement_id = publisher_helpers.create_placement_id(publisher, source_id, placement)
    return {"placement_id": placement_id, "publisher": publisher, "placement": placement, "source_id": source_id}


def make_delivery_dash_rows(delivery_dimension, objs_map):
    rows = []
    for delivery_value in objs_map.keys():
        rows.append({delivery_dimension: delivery_value})
    return rows


def make_row(target_dimension, target_id, parent):
    row = {target_dimension: target_id}
    if parent:
        row.update(parent)

    if target_dimension == "publisher_id":
        publisher, source_id = publisher_helpers.dissect_publisher_id(target_id)
        row.update({"publisher": publisher, "source_id": source_id})
    if target_dimension == "placement_id":
        publisher, source_id, placement = publisher_helpers.dissect_placement_id(target_id)
        row.update({"publisher": publisher, "placement": placement, "source_id": source_id})

    return row


def copy_fields_if_exists(field_names, source, target):
    for field_name in field_names:
        if field_name in source:
            target[field_name] = source[field_name]
