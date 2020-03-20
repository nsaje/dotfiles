from rest_framework import permissions

import core.features.bcm
import core.features.deals
import core.models
import utils.exc


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


def get_agency(user, agency_id):
    try:
        agencies = core.models.Agency.objects.all().filter_by_user(user)
        return agencies.get(id=int(agency_id))
    except core.models.Agency.DoesNotExist:
        raise utils.exc.MissingDataError("Agency does not exist")


def get_account(user, account_id, sources=None, select_related_users=False) -> core.models.Account:
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


def get_ad_group(user, ad_group_id, sources=None):
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


def get_content_ad(user, content_ad_id):
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


def get_campaign(user, campaign_id, sources=None, select_related=False):
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


def get_upload_batch(user, batch_id):
    batch = core.models.UploadBatch.objects.get(pk=batch_id)
    try:
        if batch.account_id:
            get_account(user, batch.account_id)
        else:
            get_ad_group(user, batch.ad_group_id)
        return batch
    except utils.exc.MissingDataError:
        raise utils.exc.MissingDataError("Upload batch does not exist")


def get_direct_deal(user, deal_id) -> core.features.deals.DirectDeal:
    try:
        deal = (
            core.features.deals.DirectDeal.objects.select_related("source", "agency", "account")
            .filter(id=int(deal_id))
            .get()
        )

        agency = deal.agency
        account = deal.account

        if agency is not None:
            has_access = agency.users.filter(pk=user.pk).exists()
            if not has_access:
                raise utils.exc.AuthorizationError()
        elif account is not None:
            has_access_qs = account.users.filter(pk=user.pk)
            if account.agency is not None:
                has_access_qs = has_access_qs | account.agency.users.filter(pk=user.pk)
            has_access = has_access_qs.exists()
            if not has_access:
                raise utils.exc.AuthorizationError()

        if deal.is_internal and not user.has_perm("zemauth.can_see_internal_deals"):
            raise utils.exc.AuthorizationError()

        return deal

    except core.features.deals.DirectDeal.DoesNotExist:
        raise utils.exc.MissingDataError("Deal does not exist")


def get_direct_deal_connection(user, deal_connection_id, deal) -> core.features.deals.DirectDealConnection:
    try:
        deal_connection_qs = (
            core.features.deals.DirectDealConnection.objects.select_related("deal", "account", "campaign", "adgroup")
            .filter_by_deal(deal)
            .filter(id=int(deal_connection_id))
        )
        return deal_connection_qs.get()
    except core.features.deals.DirectDealConnection.DoesNotExist:
        raise utils.exc.MissingDataError("Deal connection does not exist")


def get_credit_line_item(user, credit_id) -> core.features.bcm.CreditLineItem:
    try:
        credit = core.features.bcm.CreditLineItem.objects.prefetch_related("budgets").filter(id=int(credit_id)).get()

        agency = credit.agency
        account = credit.account

        if agency is not None:
            has_access = agency.users.filter(pk=user.pk).exists()
            if not has_access:
                raise utils.exc.AuthorizationError()
        elif account is not None:
            has_access_qs = account.users.filter(pk=user.pk)
            if account.agency is not None:
                has_access_qs = has_access_qs | account.agency.users.filter(pk=user.pk)
            has_access = has_access_qs.exists()
            if not has_access:
                raise utils.exc.AuthorizationError()

        return credit

    except core.features.bcm.CreditLineItem.DoesNotExist:
        raise utils.exc.MissingDataError("Credit does not exist")


def get_refund_line_item(user, refund_id, credit) -> core.features.bcm.RefundLineItem:
    try:
        refund_qs = (
            core.features.bcm.RefundLineItem.objects.select_related("credit", "account")
            .filter_by_credit(credit)
            .filter(id=int(refund_id))
        )
        return refund_qs.get()

    except core.features.bcm.RefundLineItem.DoesNotExist:
        raise utils.exc.MissingDataError("Refund does not exist")
