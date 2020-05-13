from django.db.models import Count
from rest_framework import permissions

import core.features.bcm
import core.features.deals
import core.features.publisher_groups
import core.models
import utils.exc
import zemauth.access


def gen_permission_class(*perms):
    class CustomPermissions(permissions.BasePermission):
        def has_permission(self, request, view):
            return bool(request.user and request.user.has_perms(perms))

    return CustomPermissions


class HasAccountAccess(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and get_account(request.user, view.kwargs["account_id"]))


class HasCampaignAccess(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and get_campaign(request.user, view.kwargs["campaign_id"]))


class HasAdGroupAccess(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and get_ad_group(request.user, view.kwargs["ad_group_id"]))


def get_agency(user, agency_id, permission: str = None):
    """
    @deprecated: use zemauth.access.get_agency
    """
    if permission:
        return zemauth.access.get_agency(user, permission, agency_id)
    try:
        agencies = core.models.Agency.objects.all().filter_by_user(user)
        return agencies.get(id=int(agency_id))
    except core.models.Agency.DoesNotExist:
        raise utils.exc.MissingDataError("Agency does not exist")


def get_account(
    user, account_id, sources=None, select_related_users=False, permission: str = None
) -> core.models.Account:
    """
    @deprecated: use zemauth.access.get_account
    """
    if permission:
        return zemauth.access.get_account(user, permission, account_id, sources, select_related_users)
    try:
        account = core.models.Account.objects.all().filter_by_user(user).select_related("settings", "agency")

        if sources:
            account = account.filter_by_sources(sources)

        if select_related_users:
            account = account.select_related("settings__default_account_manager")
            account = account.select_related("settings__default_cs_representative")
            account = account.select_related("settings__default_sales_representative")

        return account.filter(id=int(account_id)).get()
    except core.models.Account.DoesNotExist:
        raise utils.exc.MissingDataError("Account does not exist")


def get_ad_group(user, ad_group_id, sources=None, permission: str = None):
    """
    @deprecated: use zemauth.access.get_ad_group
    """
    if permission:
        return zemauth.access.get_ad_group(user, permission, ad_group_id, sources)
    try:
        ad_group = (
            core.models.AdGroup.objects.all()
            .select_related("settings", "campaign__account__agency")
            .filter_by_user(user)
            .filter(id=int(ad_group_id))
        )

        if sources:
            ad_group = ad_group.filter_by_sources(sources)

        return ad_group.get()
    except core.models.AdGroup.DoesNotExist:
        raise utils.exc.MissingDataError("Ad Group does not exist")


def get_content_ad(user, content_ad_id, permission: str = None):
    """
    @deprecated: use zemauth.access.get_content_ad
    """
    if permission:
        return zemauth.access.get_content_ad(user, permission, content_ad_id)
    try:
        content_ad = (
            core.models.ContentAd.objects.all()
            .select_related("ad_group")
            .filter_by_user(user)
            .filter(id=int(content_ad_id))
        )

        return content_ad.get()
    except core.models.AdGroup.DoesNotExist:
        raise utils.exc.MissingDataError("Content Ad does not exist")


def get_campaign(user, campaign_id, sources=None, select_related=False, permission: str = None):
    """
    @deprecated: use zemauth.access.get_campaign
    """
    if permission:
        return zemauth.access.get_campaign(user, permission, campaign_id, sources)
    try:
        campaign = (
            core.models.Campaign.objects.all()
            .select_related("settings", "account__agency")
            .filter_by_user(user)
            .filter(id=int(campaign_id))
        )
        if sources:
            campaign = campaign.filter_by_sources(sources)

        if select_related:
            campaign = campaign.select_related("account")

        return campaign.get()
    except core.models.Campaign.DoesNotExist:
        raise utils.exc.MissingDataError("Campaign does not exist")


def get_upload_batch(user, batch_id, permission: str = None):
    """
    @deprecated: use zemauth.access.get_upload_batch
    """
    if permission:
        return zemauth.access.get_upload_batch(user, permission, batch_id)
    batch = core.models.UploadBatch.objects.get(pk=batch_id)
    try:
        if batch.account_id:
            get_account(user, batch.account_id, permission=permission)
        else:
            get_ad_group(user, batch.ad_group_id, permission=permission)
        return batch
    except utils.exc.MissingDataError:
        raise utils.exc.MissingDataError("Upload batch does not exist")


def get_direct_deal(user, deal_id, permission: str = None) -> core.features.deals.DirectDeal:
    """
    @deprecated: use zemauth.access.get_direct_deal
    """
    if permission:
        return zemauth.access.get_direct_deal(user, permission, deal_id)
    try:
        deal = (
            core.features.deals.DirectDeal.objects.select_related("source", "agency", "account")
            .filter(id=int(deal_id))
            .get()
        )

        if deal.agency is not None:
            get_agency(user, deal.agency.id, permission=permission)
        elif deal.account is not None:
            get_account(user, deal.account.id, permission=permission)
        else:
            raise utils.exc.MissingDataError("Deal does not exist")

        if deal.is_internal and not user.has_perm("zemauth.can_see_internal_deals"):
            raise utils.exc.AuthorizationError()

        return deal

    except (core.features.deals.DirectDeal.DoesNotExist, utils.exc.MissingDataError):
        raise utils.exc.MissingDataError("Deal does not exist")


def get_direct_deal_connection(user, deal_connection_id, deal) -> core.features.deals.DirectDealConnection:
    return zemauth.access.get_direct_deal_connection(deal_connection_id, deal)


def get_credit_line_item(user, credit_id, permission: str = None) -> core.features.bcm.CreditLineItem:
    """
    @deprecated: use zemauth.access.get_credit_line_item
    """
    if permission:
        return zemauth.access.get_credit_line_item(user, permission, credit_id)
    try:
        credit = core.features.bcm.CreditLineItem.objects.prefetch_related("budgets").filter(id=int(credit_id)).get()

        if credit.agency is not None:
            get_agency(user, credit.agency.id, permission=permission)
        elif credit.account is not None:
            get_account(user, credit.account.id, permission=permission)
        else:
            raise utils.exc.MissingDataError("Credit does not exist")

        return credit

    except (core.features.bcm.CreditLineItem.DoesNotExist, utils.exc.MissingDataError):
        raise utils.exc.MissingDataError("Credit does not exist")


def get_refund_line_item(user, refund_id, credit) -> core.features.bcm.RefundLineItem:
    return zemauth.access.get_refund_line_item(refund_id, credit)


def get_publisher_group(user, publisher_group_id, permission: str = None, annotate_entities=False):
    """
    @deprecated: use zemauth.access.get_publisher_group
    """
    if permission:
        return zemauth.access.get_publisher_group(user, permission, publisher_group_id, annotate_entities)
    try:
        publisher_group_qs = core.features.publisher_groups.PublisherGroup.objects.all()
        if annotate_entities:
            publisher_group_qs = publisher_group_qs.annotate_entities_count()
        publisher_group = publisher_group_qs.get(id=int(publisher_group_id))

        if publisher_group.agency is not None:
            get_agency(user, publisher_group.agency.id, permission=permission)
        elif publisher_group.account is not None:
            get_account(user, publisher_group.account.id, permission=permission)
        else:
            raise utils.exc.MissingDataError("Publisher group does not exist")

        return publisher_group
    except (core.features.publisher_groups.PublisherGroup.DoesNotExist, utils.exc.MissingDataError):
        raise utils.exc.MissingDataError("Publisher group does not exist")
