from typing import Any

from django.db import models

import automation.rules
import core.features.bcm
import core.features.deals
import core.features.publisher_groups
import core.models
import utils.exc
import zemauth.features.entity_permission.helpers
import zemauth.models


def get_agency(user: zemauth.models.User, permission: str, agency_id: str) -> core.models.Agency:
    try:
        queryset_user_perm = core.models.Agency.objects.filter_by_user(user)
        queryset_entity_perm = core.models.Agency.objects.filter_by_entity_permission(user, permission)

        queryset = zemauth.features.entity_permission.helpers.log_differences_and_get_queryset(
            user, permission, queryset_user_perm, queryset_entity_perm, agency_id
        )
        return queryset.get(id=agency_id)
    except core.models.Agency.DoesNotExist:
        raise utils.exc.MissingDataError("Agency does not exist")


def get_agencies(user: zemauth.models.User, permission: str) -> models.QuerySet:
    return _get_model_queryset(user, permission, core.models.Agency)


def get_account(user: zemauth.models.User, permission: str, account_id: str, **kwargs: Any) -> core.models.Account:
    try:
        queryset_user_perm = core.models.Account.objects.filter_by_user(user).select_related("settings", "agency")
        queryset_entity_perm = core.models.Account.objects.filter_by_entity_permission(user, permission).select_related(
            "settings", "agency"
        )

        sources = kwargs.get("sources", None)
        if sources:
            queryset_user_perm = queryset_user_perm.filter_by_source(sources)
            queryset_entity_perm = queryset_entity_perm.filter_by_source(sources)

        select_related_users = kwargs.get("select_related_users", False)
        if select_related_users is True:
            paths = list(
                [
                    "settings__default_account_manager",
                    "settings__default_cs_representative",
                    "settings__default_sales_representative",
                ]
            )
            queryset_user_perm = queryset_user_perm.select_related(*paths)
            queryset_entity_perm = queryset_entity_perm.select_related(*paths)

        queryset = zemauth.features.entity_permission.helpers.log_differences_and_get_queryset(
            user, permission, queryset_user_perm, queryset_entity_perm, account_id
        )
        return queryset.get(id=account_id)
    except core.models.Account.DoesNotExist:
        raise utils.exc.MissingDataError("Account does not exist")


def get_accounts(user: zemauth.models.User, permission: str) -> models.QuerySet:
    return _get_model_queryset(user, permission, core.models.Account)


def get_campaign(user: zemauth.models.User, permission: str, campaign_id: str, **kwargs: Any) -> core.models.Campaign:
    try:
        queryset_user_perm = core.models.Campaign.objects.filter_by_user(user).select_related(
            "settings", "account__agency"
        )
        queryset_entity_perm = core.models.Campaign.objects.filter_by_entity_permission(
            user, permission
        ).select_related("settings", "account__agency")

        sources = kwargs.get("sources", None)
        if sources:
            queryset_user_perm = queryset_user_perm.filter_by_source(sources)
            queryset_entity_perm = queryset_entity_perm.filter_by_source(sources)

        queryset = zemauth.features.entity_permission.helpers.log_differences_and_get_queryset(
            user, permission, queryset_user_perm, queryset_entity_perm, campaign_id
        )
        return queryset.get(id=campaign_id)
    except core.models.Campaign.DoesNotExist:
        raise utils.exc.MissingDataError("Campaign does not exist")


def get_campaigns(user: zemauth.models.User, permission: str) -> models.QuerySet:
    return _get_model_queryset(user, permission, core.models.Campaign)


def get_ad_group(user: zemauth.models.User, permission: str, ad_group_id: str, **kwargs: Any) -> core.models.AdGroup:
    try:
        queryset_user_perm = core.models.AdGroup.objects.filter_by_user(user).select_related(
            "settings", "campaign__account__agency"
        )
        queryset_entity_perm = core.models.AdGroup.objects.filter_by_entity_permission(user, permission).select_related(
            "settings", "campaign__account__agency"
        )

        sources = kwargs.get("sources", None)
        if sources:
            queryset_user_perm = queryset_user_perm.filter_by_source(sources)
            queryset_entity_perm = queryset_entity_perm.filter_by_source(sources)

        queryset = zemauth.features.entity_permission.helpers.log_differences_and_get_queryset(
            user, permission, queryset_user_perm, queryset_entity_perm, ad_group_id
        )
        return queryset.get(id=ad_group_id)
    except core.models.AdGroup.DoesNotExist:
        raise utils.exc.MissingDataError("Ad Group does not exist")


def get_ad_groups(user: zemauth.models.User, permission: str) -> models.QuerySet:
    return _get_model_queryset(user, permission, core.models.AdGroup)


def get_content_ad(user: zemauth.models.User, permission: str, content_ad_id: str) -> core.models.ContentAd:
    try:
        queryset_user_perm = core.models.ContentAd.objects.filter_by_user(user).select_related("ad_group")
        queryset_entity_perm = core.models.ContentAd.objects.filter_by_entity_permission(
            user, permission
        ).select_related("ad_group")

        queryset = zemauth.features.entity_permission.helpers.log_differences_and_get_queryset(
            user, permission, queryset_user_perm, queryset_entity_perm, content_ad_id
        )
        return queryset.get(id=content_ad_id)
    except core.models.ContentAd.DoesNotExist:
        raise utils.exc.MissingDataError("Content Ad does not exist")


def get_content_ads(user: zemauth.models.User, permission: str) -> models.QuerySet:
    return _get_model_queryset(user, permission, core.models.ContentAd)


def get_upload_batch(user: zemauth.models.User, permission: str, batch_id: str) -> core.models.UploadBatch:
    try:
        batch = core.models.UploadBatch.objects.get(pk=batch_id)
        if batch.account_id:
            get_account(user, permission, batch.account_id)
        else:
            get_ad_group(user, permission, batch.ad_group_id)
        return batch
    except (core.models.UploadBatch.DoesNotExist, utils.exc.MissingDataError):
        raise utils.exc.MissingDataError("Upload batch does not exist")


def get_direct_deal(user: zemauth.models.User, permission: str, deal_id: str) -> core.features.deals.DirectDeal:
    try:
        queryset_user_perm = core.features.deals.DirectDeal.objects.filter_by_user(user).select_related(
            "source", "agency", "account"
        )
        queryset_entity_perm = core.features.deals.DirectDeal.objects.filter_by_entity_permission(
            user, permission
        ).select_related("source", "agency", "account")

        queryset = zemauth.features.entity_permission.helpers.log_differences_and_get_queryset(
            user, permission, queryset_user_perm, queryset_entity_perm, deal_id
        )
        deal = queryset.get(id=deal_id)

        if deal.is_internal and not user.has_perm("zemauth.can_see_internal_deals"):
            raise utils.exc.AuthorizationError()
        return deal
    except core.features.deals.DirectDeal.DoesNotExist:
        raise utils.exc.MissingDataError("Deal does not exist")


def get_direct_deals(user: zemauth.models.User, permission: str) -> models.QuerySet:
    return _get_model_queryset(user, permission, core.features.deals.DirectDeal)


def get_direct_deal_connection(
    deal_connection_id: str, deal: core.features.deals.DirectDeal
) -> core.features.deals.DirectDealConnection:
    try:
        deal_connection = (
            core.features.deals.DirectDealConnection.objects.select_related("deal", "account", "campaign", "adgroup")
            .filter_by_deal(deal)
            .get(id=deal_connection_id)
        )
        return deal_connection
    except core.features.deals.DirectDealConnection.DoesNotExist:
        raise utils.exc.MissingDataError("Deal connection does not exist")


def get_credit_line_item(
    user: zemauth.models.User, permission: str, credit_id: str
) -> core.features.bcm.CreditLineItem:
    try:
        credit = core.features.bcm.CreditLineItem.objects.prefetch_related("budgets").get(id=credit_id)
        if credit.agency_id:
            get_agency(user, permission, credit.agency_id)
        else:
            get_account(user, permission, credit.account_id)
        return credit
    except (core.features.bcm.CreditLineItem.DoesNotExist, utils.exc.MissingDataError):
        raise utils.exc.MissingDataError("Credit does not exist")


def get_refund_line_item(refund_id: str, credit: core.features.bcm.CreditLineItem) -> core.features.bcm.RefundLineItem:
    try:
        refund = (
            core.features.bcm.RefundLineItem.objects.select_related("credit", "account")
            .filter_by_credit(credit)
            .get(id=refund_id)
        )
        return refund
    except core.features.bcm.RefundLineItem.DoesNotExist:
        raise utils.exc.MissingDataError("Refund does not exist")


def get_publisher_group(user: zemauth.models.User, permission: str, publisher_group_id: str, **kwargs: Any):
    try:
        queryset_user_perm = core.features.publisher_groups.PublisherGroup.objects.filter_by_user(user)
        queryset_entity_perm = core.features.publisher_groups.PublisherGroup.objects.filter_by_entity_permission(
            user, permission
        )

        queryset = zemauth.features.entity_permission.helpers.log_differences_and_get_queryset(
            user, permission, queryset_user_perm, queryset_entity_perm, publisher_group_id
        )

        annotate_entities = kwargs.get("annotate_entities", None)
        if annotate_entities:
            queryset = queryset.annotate_entities_count()

        return queryset.get(id=publisher_group_id)
    except core.features.publisher_groups.PublisherGroup.DoesNotExist:
        raise utils.exc.MissingDataError("Publisher group does not exist")


def get_publisher_groups(user: zemauth.models.User, permission: str) -> models.QuerySet:
    return _get_model_queryset(user, permission, core.features.publisher_groups.PublisherGroup)


def _get_model_queryset(user: zemauth.models.User, permission: str, model: models.Model) -> models.QuerySet:
    queryset_user_perm = model.objects.filter_by_user(user)
    queryset_entity_perm = model.objects.filter_by_entity_permission(user, permission)
    return zemauth.features.entity_permission.helpers.log_differences_and_get_queryset(
        user, permission, queryset_user_perm, queryset_entity_perm
    )


def get_automation_rule(user: zemauth.models.User, permission: str, rule_id: str) -> automation.rules.Rule:
    try:
        if not user.has_perm("zemauth.fea_can_create_automation_rules"):
            raise utils.exc.AuthorizationError()

        queryset_user_perm = automation.rules.Rule.objects.filter_by_user(user).select_related("agency", "account")
        queryset_entity_perm = automation.rules.Rule.objects.filter_by_entity_permission(
            user, permission
        ).select_related("agency", "account")

        queryset = zemauth.features.entity_permission.helpers.log_differences_and_get_queryset(
            user, permission, queryset_user_perm, queryset_entity_perm, rule_id
        )
        rule = queryset.get(id=rule_id)

        return rule
    except automation.rules.Rule.DoesNotExist:
        raise utils.exc.MissingDataError("Rule does not exist")
