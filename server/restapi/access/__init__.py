from rest_framework import permissions

import core.entity
import utils.exc


def gen_permission_class(*perms):
    class CustomPermissions(permissions.BasePermission):
        def has_permission(self, request, view):
            return bool(request.user and request.user.has_perms(perms))
    return CustomPermissions


class HasAccountAccess(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and get_account(request.user, view.kwargs['account_id']))


class HasCampaignAccess(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and get_campaign(request.user, view.kwargs['campaign_id']))


class HasAdGroupAccess(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and get_ad_group(request.user, view.kwargs['ad_group_id']))


def get_agency(user, agency_id):
    try:
        agencies = core.entity.Agency.objects.all().filter_by_user(user)
        return agencies.get(id=int(agency_id))
    except core.entity.Agency.DoesNotExist:
        raise utils.exc.MissingDataError('Agency does not exist')


def get_account(user, account_id, sources=None):
    try:
        account = core.entity.Account.objects.all().filter_by_user(user).select_related('settings')

        if sources:
            account = account.filter_by_sources(sources)

        return account.filter(id=int(account_id)).get()
    except core.entity.Account.DoesNotExist:
        raise utils.exc.MissingDataError('Account does not exist')


def get_ad_group(user, ad_group_id, select_related=False, sources=None):
    try:
        ad_group = core.entity.AdGroup.objects.all()\
                                              .select_related('settings')\
                                              .filter_by_user(user)\
                                              .filter(id=int(ad_group_id))

        if sources:
            ad_group = ad_group.filter_by_sources(sources)

        if select_related:
            ad_group = ad_group.select_related('campaign__account')

        return ad_group.get()
    except core.entity.AdGroup.DoesNotExist:
        raise utils.exc.MissingDataError('Ad Group does not exist')


def get_content_ad(user, content_ad_id, select_related=False):
    try:
        content_ad = core.entity.ContentAd.objects.all().filter_by_user(user). \
            filter(id=int(content_ad_id))

        if select_related:
            content_ad = content_ad.select_related('ad_group')

        return content_ad.get()
    except core.entity.AdGroup.DoesNotExist:
        raise utils.exc.MissingDataError('Content Ad does not exist')


def get_campaign(user, campaign_id, sources=None, select_related=False):
    try:
        campaign = core.entity.Campaign.objects.all()\
                                               .select_related('settings')\
                                               .filter_by_user(user)\
                                               .filter(id=int(campaign_id))
        if sources:
            campaign = campaign.filter_by_sources(sources)

        if select_related:
            campaign = campaign.select_related('account')

        return campaign.get()
    except core.entity.Campaign.DoesNotExist:
        raise utils.exc.MissingDataError('Campaign does not exist')


def get_upload_batch(user, batch_id):
    batch = core.entity.UploadBatch.objects.get(pk=batch_id)
    try:
        if batch.account_id:
            get_account(user, batch.account_id)
        else:
            get_ad_group(user, batch.ad_group_id)
        return batch
    except utils.exc.MissingDataError:
        raise utils.exc.MissingDataError('Upload batch does not exist')
