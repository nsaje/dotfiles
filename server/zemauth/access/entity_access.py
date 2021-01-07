from typing import Any

from django.db import models
from django.db.models import QuerySet

import automation.rules
import core.features.bcm
import core.features.creatives
import core.features.deals
import core.features.publisher_groups
import core.models
import utils.exc
import zemauth.models
from zemauth.features.entity_permission import Permission


def get_agency(user: zemauth.models.User, permission: str, agency_id: str) -> core.models.Agency:
    try:
        queryset = core.models.Agency.objects.filter_by_entity_permission(user, permission)
        return queryset.get(id=agency_id)
    except core.models.Agency.DoesNotExist:
        raise utils.exc.MissingDataError("Agency does not exist")


def get_agencies(user: zemauth.models.User, permission: str) -> models.QuerySet:
    return _get_model_queryset(user, permission, core.models.Agency)


def get_account(user: zemauth.models.User, permission: str, account_id: str, **kwargs: Any) -> core.models.Account:
    try:
        queryset = core.models.Account.objects.filter_by_entity_permission(user, permission).select_related(
            "settings", "agency"
        )

        sources = kwargs.get("sources", None)
        if sources:
            queryset = queryset.filter_by_sources(sources)

        select_related_users = kwargs.get("select_related_users", False)
        if select_related_users is True:
            paths = list(
                [
                    "settings__default_account_manager",
                    "settings__default_cs_representative",
                    "settings__default_sales_representative",
                ]
            )
            queryset = queryset.select_related(*paths)

        return queryset.get(id=account_id)
    except core.models.Account.DoesNotExist:
        raise utils.exc.MissingDataError("Account does not exist")


def get_accounts(user: zemauth.models.User, permission: str) -> models.QuerySet:
    return _get_model_queryset(user, permission, core.models.Account)


def get_campaign(user: zemauth.models.User, permission: str, campaign_id: str, **kwargs: Any) -> core.models.Campaign:
    try:
        queryset = core.models.Campaign.objects.filter_by_entity_permission(user, permission).select_related(
            "settings", "account__agency"
        )

        sources = kwargs.get("sources", None)
        if sources:
            queryset = queryset.filter_by_sources(sources)

        return queryset.get(id=campaign_id)
    except core.models.Campaign.DoesNotExist:
        raise utils.exc.MissingDataError("Campaign does not exist")


def get_campaigns(user: zemauth.models.User, permission: str) -> models.QuerySet:
    return _get_model_queryset(user, permission, core.models.Campaign)


def get_ad_group(user: zemauth.models.User, permission: str, ad_group_id: str, **kwargs: Any) -> core.models.AdGroup:
    try:
        queryset = core.models.AdGroup.objects.filter_by_entity_permission(user, permission).select_related(
            "settings", "campaign__account__agency"
        )

        sources = kwargs.get("sources", None)
        if sources:
            queryset = queryset.filter_by_sources(sources)

        return queryset.get(id=ad_group_id)
    except core.models.AdGroup.DoesNotExist:
        raise utils.exc.MissingDataError("Ad Group does not exist")


def get_ad_groups(user: zemauth.models.User, permission: str) -> models.QuerySet:
    return _get_model_queryset(user, permission, core.models.AdGroup)


def get_content_ad(user: zemauth.models.User, permission: str, content_ad_id: str) -> core.models.ContentAd:
    try:
        queryset = core.models.ContentAd.objects.filter_by_entity_permission(user, permission).select_related(
            "ad_group"
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
        queryset = core.features.deals.DirectDeal.objects.filter_by_entity_permission(user, permission).select_related(
            "source", "agency", "account"
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
    user: zemauth.models.User, permission: str, credit_id: str, **kwargs: Any
) -> core.features.bcm.CreditLineItem:
    try:
        credit_qs = core.features.bcm.CreditLineItem.objects.all()
        prefetch_related_budgets = kwargs.get("prefetch_related_budgets", False)
        if prefetch_related_budgets is True:
            credit_qs = credit_qs.prefetch_related("budgets")
        credit = credit_qs.get(id=credit_id)
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
        queryset = core.features.publisher_groups.PublisherGroup.objects.filter_by_entity_permission(user, permission)

        annotate_entities = kwargs.get("annotate_entities", None)
        if annotate_entities:
            queryset = queryset.annotate_entities_count()

        return queryset.get(id=publisher_group_id)
    except core.features.publisher_groups.PublisherGroup.DoesNotExist:
        raise utils.exc.MissingDataError("Publisher group does not exist")


def get_publisher_groups(user: zemauth.models.User, permission: str) -> models.QuerySet:
    return _get_model_queryset(user, permission, core.features.publisher_groups.PublisherGroup)


def get_user(
    calling_user: zemauth.models.User,
    user_id: int,
    account: core.models.Account = None,
    agency: core.models.Agency = None,
    permission: str = Permission.READ,
) -> zemauth.models.User:
    try:
        user_qs: QuerySet = zemauth.models.User.objects
        requested_user_qs: QuerySet = None

        if account is not None:
            requested_user_qs = user_qs.filter_by_account(account)
        elif agency is not None:
            requested_user_qs = user_qs.filter_by_agency_and_related_accounts(agency)
        elif not calling_user.has_perm_on_all_entities(permission):
            raise utils.exc.ValidationError("Agency or account must be specified")

        if calling_user.has_perm_on_all_entities(permission):
            if requested_user_qs:
                requested_user_qs |= user_qs.filter_by_internal()
            else:
                requested_user_qs = user_qs.all()

        requested_user: zemauth.models.User = requested_user_qs.distinct().get(pk=user_id)
        return requested_user
    except zemauth.models.User.DoesNotExist:
        raise utils.exc.MissingDataError("User does not exist")


def _get_model_queryset(user: zemauth.models.User, permission: str, model: models.Model) -> models.QuerySet:
    return model.objects.filter_by_entity_permission(user, permission)


def get_automation_rule(user: zemauth.models.User, permission: str, rule_id: str) -> automation.rules.Rule:
    try:
        if not user.has_perm("zemauth.fea_can_create_automation_rules"):
            raise utils.exc.AuthorizationError()

        queryset = automation.rules.Rule.objects.filter_by_entity_permission(user, permission).select_related(
            "agency", "account"
        )

        rule = queryset.get(id=rule_id)

        return rule
    except automation.rules.Rule.DoesNotExist:
        raise utils.exc.MissingDataError("Rule does not exist")


def get_conversion_pixel(user: zemauth.models.User, permission: str, pixel_id: str) -> core.models.ConversionPixel:
    try:
        pixel = core.models.ConversionPixel.objects.get(pk=pixel_id)
        if pixel.account_id:
            get_account(user, permission, pixel.account_id)
        return pixel
    except (core.models.ConversionPixel.DoesNotExist, utils.exc.MissingDataError):
        raise utils.exc.MissingDataError("Conversion pixel does not exist")


def get_creative(user: zemauth.models.User, permission: str, creative_id: str) -> core.features.creatives.Creative:
    try:
        queryset = core.features.creatives.Creative.objects.filter_by_entity_permission(
            user, permission
        ).select_related("agency", "account")
        return queryset.get(id=creative_id)
    except core.features.creatives.Creative.DoesNotExist:
        raise utils.exc.MissingDataError("Creative does not exist")
