import datetime

import mock
from django.db import models
from django.test import TestCase

import core.features.bcm
import core.features.deals
import core.features.publisher_groups
import core.models
import utils.exc
import zemauth.features.entity_permission
import zemauth.models
from utils import test_helper
from utils.magic_mixer import magic_mixer

from . import entity_access


class ObjectAccessTestCaseMixin(object):
    def side_effect_log_differences_and_get_queryset(
        self,
        user: zemauth.models.User,
        permission: str,
        user_permission_queryset: models.QuerySet,
        entity_permission_queryset: models.QuerySet,
        entity_id: str = None,
    ) -> models.QuerySet:
        return entity_permission_queryset

    def _for_all_entities(self, user: zemauth.models.User, permission: str, entity_access_fn, model: models.Model):
        user.entitypermission_set.all().delete()
        magic_mixer.blend(
            zemauth.features.entity_permission.EntityPermission,
            user=user,
            agency=None,
            account=None,
            permission=permission,
        )

        result = entity_access_fn(user, permission, model.id)
        self.assertEqual(model.id, result.id)

    def _for_agency(
        self,
        user: zemauth.models.User,
        permission: str,
        entity_access_fn,
        agency: core.models.Agency,
        model: models.Model,
    ):
        user.entitypermission_set.all().delete()
        magic_mixer.blend(
            zemauth.features.entity_permission.EntityPermission,
            user=user,
            agency=agency,
            account=None,
            permission=permission,
        )

        result = entity_access_fn(user, permission, model.id)
        self.assertEqual(model.id, result.id)

    def _for_account(
        self,
        user: zemauth.models.User,
        permission: str,
        entity_access_fn,
        account: core.models.Account,
        model: models.Model,
        has_agency_scope: bool,
    ):
        user.entitypermission_set.all().delete()
        magic_mixer.blend(
            zemauth.features.entity_permission.EntityPermission,
            user=user,
            agency=None,
            account=account,
            permission=permission,
        )

        if has_agency_scope:
            """
            If model has agency scope, having account
            permission is not enough. We must assert
            that we can't access it.
            """
            with self.assertRaises(utils.exc.MissingDataError):
                entity_access_fn(user, permission, model.id)
        else:
            result = entity_access_fn(user, permission, model.id)
            self.assertEqual(model.id, result.id)

    def _for_none(self, user: zemauth.models.User, permission: str, entity_access_fn, model: models.Model):
        user.entitypermission_set.all().delete()
        with self.assertRaises(utils.exc.MissingDataError):
            entity_access_fn(user, permission, model.id)
        with self.assertRaises(utils.exc.MissingDataError):
            entity_access_fn(user, permission, None)


class AgencyAccessTestCase(ObjectAccessTestCaseMixin, TestCase):
    @mock.patch("zemauth.features.entity_permission.helpers.log_differences_and_get_queryset")
    def test_get_agency(self, mock_log_differences_and_get_queryset):
        mock_log_differences_and_get_queryset.side_effect = self.side_effect_log_differences_and_get_queryset

        agency: core.models.Agency = magic_mixer.blend(core.models.Agency)
        account: core.models.Account = magic_mixer.blend(core.models.Account, agency=agency)
        user: zemauth.models.User = magic_mixer.blend_user()

        for permission in zemauth.features.entity_permission.Permission.get_all():
            self._for_all_entities(user, permission, entity_access.get_agency, agency)
            self._for_agency(user, permission, entity_access.get_agency, agency, agency)
            self._for_account(user, permission, entity_access.get_agency, account, agency, True)
            self._for_none(user, permission, entity_access.get_agency, agency)


class AccountAccessTestCase(ObjectAccessTestCaseMixin, TestCase):
    @mock.patch("zemauth.features.entity_permission.helpers.log_differences_and_get_queryset")
    def test_get_account(self, mock_log_differences_and_get_queryset):
        mock_log_differences_and_get_queryset.side_effect = self.side_effect_log_differences_and_get_queryset

        agency: core.models.Agency = magic_mixer.blend(core.models.Agency)
        account: core.models.Account = magic_mixer.blend(core.models.Account, agency=agency)
        user: zemauth.models.User = magic_mixer.blend_user()

        for permission in zemauth.features.entity_permission.Permission.get_all():
            self._for_all_entities(user, permission, entity_access.get_account, account)
            self._for_agency(user, permission, entity_access.get_account, agency, account)
            self._for_account(user, permission, entity_access.get_account, account, account, False)
            self._for_none(user, permission, entity_access.get_account, account)


class CampaignAccessTestCase(ObjectAccessTestCaseMixin, TestCase):
    @mock.patch("zemauth.features.entity_permission.helpers.log_differences_and_get_queryset")
    def test_get_campaign(self, mock_log_differences_and_get_queryset):
        mock_log_differences_and_get_queryset.side_effect = self.side_effect_log_differences_and_get_queryset

        agency: core.models.Agency = magic_mixer.blend(core.models.Agency)
        account: core.models.Account = magic_mixer.blend(core.models.Account, agency=agency)
        campaign: core.models.Campaign = magic_mixer.blend(core.models.Campaign, account=account)
        user: zemauth.models.User = magic_mixer.blend_user()

        for permission in zemauth.features.entity_permission.Permission.get_all():
            self._for_all_entities(user, permission, entity_access.get_campaign, campaign)
            self._for_agency(user, permission, entity_access.get_campaign, agency, campaign)
            self._for_account(user, permission, entity_access.get_campaign, account, campaign, False)
            self._for_none(user, permission, entity_access.get_campaign, campaign)


class AdGroupAccessTestCase(ObjectAccessTestCaseMixin, TestCase):
    @mock.patch("zemauth.features.entity_permission.helpers.log_differences_and_get_queryset")
    def test_get_ad_group(self, mock_log_differences_and_get_queryset):
        mock_log_differences_and_get_queryset.side_effect = self.side_effect_log_differences_and_get_queryset

        agency: core.models.Agency = magic_mixer.blend(core.models.Agency)
        account: core.models.Account = magic_mixer.blend(core.models.Account, agency=agency)
        campaign: core.models.Campaign = magic_mixer.blend(core.models.Campaign, account=account)
        ad_group: core.models.AdGroup = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        user: zemauth.models.User = magic_mixer.blend_user()

        for permission in zemauth.features.entity_permission.Permission.get_all():
            self._for_all_entities(user, permission, entity_access.get_ad_group, ad_group)
            self._for_agency(user, permission, entity_access.get_ad_group, agency, ad_group)
            self._for_account(user, permission, entity_access.get_ad_group, account, ad_group, False)
            self._for_none(user, permission, entity_access.get_ad_group, ad_group)


class ContentAdAccessTestCase(ObjectAccessTestCaseMixin, TestCase):
    @mock.patch("zemauth.features.entity_permission.helpers.log_differences_and_get_queryset")
    def test_get_content_ad(self, mock_log_differences_and_get_queryset):
        mock_log_differences_and_get_queryset.side_effect = self.side_effect_log_differences_and_get_queryset

        agency: core.models.Agency = magic_mixer.blend(core.models.Agency)
        account: core.models.Account = magic_mixer.blend(core.models.Account, agency=agency)
        campaign: core.models.Campaign = magic_mixer.blend(core.models.Campaign, account=account)
        ad_group: core.models.AdGroup = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        content_ad: core.models.ContentAd = magic_mixer.blend(core.models.ContentAd, ad_group=ad_group)
        user: zemauth.models.User = magic_mixer.blend_user()

        for permission in zemauth.features.entity_permission.Permission.get_all():
            self._for_all_entities(user, permission, entity_access.get_content_ad, content_ad)
            self._for_agency(user, permission, entity_access.get_content_ad, agency, content_ad)
            self._for_account(user, permission, entity_access.get_content_ad, account, content_ad, False)
            self._for_none(user, permission, entity_access.get_content_ad, content_ad)


class UploadBatchAccessTestCase(ObjectAccessTestCaseMixin, TestCase):
    @mock.patch("zemauth.features.entity_permission.helpers.log_differences_and_get_queryset")
    def test_get_upload_batch(self, mock_log_differences_and_get_queryset):
        mock_log_differences_and_get_queryset.side_effect = self.side_effect_log_differences_and_get_queryset

        agency: core.models.Agency = magic_mixer.blend(core.models.Agency)
        account: core.models.Account = magic_mixer.blend(core.models.Account, agency=agency)
        campaign: core.models.Campaign = magic_mixer.blend(core.models.Campaign, account=account)
        ad_group: core.models.AdGroup = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        batch: core.models.UploadBatch = magic_mixer.blend(core.models.UploadBatch, ad_group=ad_group, account=None)
        user: zemauth.models.User = magic_mixer.blend_user()

        for permission in zemauth.features.entity_permission.Permission.get_all():
            self._for_all_entities(user, permission, entity_access.get_upload_batch, batch)
            self._for_agency(user, permission, entity_access.get_upload_batch, agency, batch)
            self._for_account(user, permission, entity_access.get_upload_batch, account, batch, False)
            self._for_none(user, permission, entity_access.get_upload_batch, batch)


class DirectDealAccessTestCase(ObjectAccessTestCaseMixin, TestCase):
    @mock.patch("zemauth.features.entity_permission.helpers.log_differences_and_get_queryset")
    def test_get_direct_deal(self, mock_log_differences_and_get_queryset):
        mock_log_differences_and_get_queryset.side_effect = self.side_effect_log_differences_and_get_queryset

        agency: core.models.Agency = magic_mixer.blend(core.models.Agency)
        account: core.models.Account = magic_mixer.blend(core.models.Account, agency=agency)
        deal_with_agency_scope: core.features.deals.DirectDeal = magic_mixer.blend(
            core.features.deals.DirectDeal, agency=agency
        )
        deal_with_account_scope: core.features.deals.DirectDeal = magic_mixer.blend(
            core.features.deals.DirectDeal, account=account
        )
        user: zemauth.models.User = magic_mixer.blend_user()

        for permission in zemauth.features.entity_permission.Permission.get_all():
            self._for_all_entities(user, permission, entity_access.get_direct_deal, deal_with_agency_scope)
            self._for_agency(user, permission, entity_access.get_direct_deal, agency, deal_with_agency_scope)
            self._for_account(user, permission, entity_access.get_direct_deal, account, deal_with_agency_scope, True)
            self._for_none(user, permission, entity_access.get_direct_deal, deal_with_agency_scope)

            self._for_all_entities(user, permission, entity_access.get_direct_deal, deal_with_account_scope)
            self._for_agency(user, permission, entity_access.get_direct_deal, agency, deal_with_account_scope)
            self._for_account(user, permission, entity_access.get_direct_deal, account, deal_with_account_scope, False)
            self._for_none(user, permission, entity_access.get_direct_deal, deal_with_account_scope)

    @mock.patch("zemauth.features.entity_permission.helpers.log_differences_and_get_queryset")
    def test_has_internal_deal_access_no_permission(self, mock_log_differences_and_get_queryset):
        mock_log_differences_and_get_queryset.side_effect = self.side_effect_log_differences_and_get_queryset

        user: zemauth.models.User = magic_mixer.blend_user()
        permission: str = zemauth.features.entity_permission.constants.Permission.READ
        agency = magic_mixer.blend(core.models.Agency)
        deal: core.features.deals.DirectDeal = magic_mixer.blend(
            core.features.deals.DirectDeal, is_internal=True, agency=agency
        )
        magic_mixer.blend(
            zemauth.features.entity_permission.EntityPermission,
            user=user,
            agency=agency,
            account=None,
            permission=permission,
        )

        with self.assertRaises(utils.exc.AuthorizationError):
            entity_access.get_direct_deal(user, permission, deal.id)

    @mock.patch("zemauth.features.entity_permission.helpers.log_differences_and_get_queryset")
    def test_has_internal_deal_access_permission(self, mock_log_differences_and_get_queryset):
        mock_log_differences_and_get_queryset.side_effect = self.side_effect_log_differences_and_get_queryset

        user: zemauth.models.User = magic_mixer.blend_user()
        test_helper.add_permissions(user, ["can_see_internal_deals"])
        permission: str = zemauth.features.entity_permission.constants.Permission.READ
        agency = magic_mixer.blend(core.models.Agency)
        deal: core.features.deals.DirectDeal = magic_mixer.blend(
            core.features.deals.DirectDeal, is_internal=True, agency=agency
        )
        magic_mixer.blend(
            zemauth.features.entity_permission.EntityPermission,
            user=user,
            agency=agency,
            account=None,
            permission=permission,
        )

        result = entity_access.get_direct_deal(user, permission, deal.id)
        self.assertEqual(result.id, deal.id)


class CreditLineItemAccessTestCase(ObjectAccessTestCaseMixin, TestCase):
    @mock.patch("zemauth.features.entity_permission.helpers.log_differences_and_get_queryset")
    def test_get_credit_line_item(self, mock_log_differences_and_get_queryset):
        mock_log_differences_and_get_queryset.side_effect = self.side_effect_log_differences_and_get_queryset

        agency: core.models.Agency = magic_mixer.blend(core.models.Agency)
        account: core.models.Account = magic_mixer.blend(core.models.Account, agency=agency)
        credit_with_agency_scope: core.features.bcm.CreditLineItem = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            agency=agency,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
        )
        credit_with_account_scope: core.features.bcm.CreditLineItem = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            account=account,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(30),
        )
        user: zemauth.models.User = magic_mixer.blend_user()

        for permission in zemauth.features.entity_permission.Permission.get_all():
            self._for_all_entities(user, permission, entity_access.get_credit_line_item, credit_with_agency_scope)
            self._for_agency(user, permission, entity_access.get_credit_line_item, agency, credit_with_agency_scope)
            self._for_account(
                user, permission, entity_access.get_credit_line_item, account, credit_with_agency_scope, True
            )
            self._for_none(user, permission, entity_access.get_credit_line_item, credit_with_agency_scope)

            self._for_all_entities(user, permission, entity_access.get_credit_line_item, credit_with_account_scope)
            self._for_agency(user, permission, entity_access.get_credit_line_item, agency, credit_with_account_scope)
            self._for_account(
                user, permission, entity_access.get_credit_line_item, account, credit_with_account_scope, False
            )
            self._for_none(user, permission, entity_access.get_credit_line_item, credit_with_account_scope)


class PublisherGroupAccessTestCase(ObjectAccessTestCaseMixin, TestCase):
    @mock.patch("zemauth.features.entity_permission.helpers.log_differences_and_get_queryset")
    def test_get_publisher_group(self, mock_log_differences_and_get_queryset):
        mock_log_differences_and_get_queryset.side_effect = self.side_effect_log_differences_and_get_queryset

        agency: core.models.Agency = magic_mixer.blend(core.models.Agency)
        account: core.models.Account = magic_mixer.blend(core.models.Account, agency=agency)
        publisher_group_with_agency_scope: core.features.publisher_groups.PublisherGroup = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroup, agency=agency
        )
        publisher_group_with_account_scope: core.features.publisher_groups.PublisherGroup = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroup, account=account
        )
        user: zemauth.models.User = magic_mixer.blend_user()

        for permission in zemauth.features.entity_permission.Permission.get_all():
            self._for_all_entities(
                user, permission, entity_access.get_publisher_group, publisher_group_with_agency_scope
            )
            self._for_agency(
                user, permission, entity_access.get_publisher_group, agency, publisher_group_with_agency_scope
            )
            self._for_account(
                user, permission, entity_access.get_publisher_group, account, publisher_group_with_agency_scope, True
            )
            self._for_none(user, permission, entity_access.get_publisher_group, publisher_group_with_agency_scope)

            self._for_all_entities(
                user, permission, entity_access.get_publisher_group, publisher_group_with_account_scope
            )
            self._for_agency(
                user, permission, entity_access.get_publisher_group, agency, publisher_group_with_account_scope
            )
            self._for_account(
                user, permission, entity_access.get_publisher_group, account, publisher_group_with_account_scope, False
            )
            self._for_none(user, permission, entity_access.get_publisher_group, publisher_group_with_account_scope)
