import datetime

from django.db import models
from django.test import TestCase

import automation.rules
import core.features.bcm
import core.features.creatives
import core.features.deals
import core.features.publisher_groups
import core.models
import utils.exc
import zemauth.features.entity_permission
import zemauth.models
from utils import test_helper
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission

from . import entity_access
from .entity_access import get_user


class ObjectAccessTestCaseMixin(object):
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
    def test_get_agency(self):
        agency: core.models.Agency = magic_mixer.blend(core.models.Agency)
        account: core.models.Account = magic_mixer.blend(core.models.Account, agency=agency)
        user: zemauth.models.User = magic_mixer.blend_user()

        for permission in zemauth.features.entity_permission.Permission.get_all():
            self._for_all_entities(user, permission, entity_access.get_agency, agency)
            self._for_agency(user, permission, entity_access.get_agency, agency, agency)
            self._for_account(user, permission, entity_access.get_agency, account, agency, True)
            self._for_none(user, permission, entity_access.get_agency, agency)


class AccountAccessTestCase(ObjectAccessTestCaseMixin, TestCase):
    def test_get_account(self):
        agency: core.models.Agency = magic_mixer.blend(core.models.Agency)
        account: core.models.Account = magic_mixer.blend(core.models.Account, agency=agency)
        user: zemauth.models.User = magic_mixer.blend_user()

        for permission in zemauth.features.entity_permission.Permission.get_all():
            self._for_all_entities(user, permission, entity_access.get_account, account)
            self._for_agency(user, permission, entity_access.get_account, agency, account)
            self._for_account(user, permission, entity_access.get_account, account, account, False)
            self._for_none(user, permission, entity_access.get_account, account)


class CampaignAccessTestCase(ObjectAccessTestCaseMixin, TestCase):
    def test_get_campaign(self):
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
    def test_get_ad_group(self):
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
    def test_get_content_ad(self):
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
    def test_get_upload_batch(self):
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
    def test_get_direct_deal(self):
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

    def test_has_internal_deal_access_no_permission(self):
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

    def test_has_internal_deal_access_permission(self):
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
    def test_get_credit_line_item(self):
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
    def test_get_publisher_group(self):
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


class AutomationRuleAccessTestCase(ObjectAccessTestCaseMixin, TestCase):
    def test_get_automation_rule(self):
        agency: core.models.Agency = magic_mixer.blend(core.models.Agency)
        account: core.models.Account = magic_mixer.blend(core.models.Account, agency=agency)
        rule_with_agency_scope: core.features.publisher_groups.PublisherGroup = magic_mixer.blend(
            automation.rules.Rule, agency=agency
        )
        rule_with_account_scope: core.features.publisher_groups.PublisherGroup = magic_mixer.blend(
            automation.rules.Rule, account=account
        )
        user: zemauth.models.User = magic_mixer.blend_user()
        test_helper.add_permissions(user, ["fea_can_create_automation_rules"])

        for permission in zemauth.features.entity_permission.Permission.get_all():
            self._for_all_entities(user, permission, entity_access.get_automation_rule, rule_with_agency_scope)
            self._for_agency(user, permission, entity_access.get_automation_rule, agency, rule_with_agency_scope)
            self._for_account(
                user, permission, entity_access.get_automation_rule, account, rule_with_agency_scope, True
            )
            self._for_none(user, permission, entity_access.get_automation_rule, rule_with_agency_scope)

            self._for_all_entities(user, permission, entity_access.get_automation_rule, rule_with_account_scope)
            self._for_agency(user, permission, entity_access.get_automation_rule, agency, rule_with_account_scope)
            self._for_account(
                user, permission, entity_access.get_automation_rule, account, rule_with_account_scope, False
            )
            self._for_none(user, permission, entity_access.get_automation_rule, rule_with_account_scope)


class UserAccessTestCase(TestCase):
    def setUp(self) -> None:
        self.request = magic_mixer.blend_request_user()
        self.calling_user: zemauth.models.User = self.request.user
        self.requested_user: zemauth.models.User = magic_mixer.blend_user()

    def test_get_user_by_agency(self):
        agency = magic_mixer.blend(core.models.Agency)
        test_helper.add_entity_permissions(self.requested_user, [Permission.READ], agency)

        user_from_method = get_user(self.calling_user, self.requested_user.id, None, agency)
        self.assertEqual(user_from_method, self.requested_user)

    def test_get_user_by_account(self):
        account = magic_mixer.blend(core.models.Account)
        test_helper.add_entity_permissions(self.requested_user, [Permission.READ], account)

        user_from_method = get_user(self.calling_user, self.requested_user.id, account, None)
        self.assertEqual(user_from_method, self.requested_user)

    def test_get_user_no_user_permission(self):
        agency = magic_mixer.blend(core.models.Agency)
        test_helper.add_entity_permissions(self.calling_user, [Permission.READ, Permission.USER], agency)

        self.assertRaises(
            utils.exc.MissingDataError,
            get_user,
            calling_user=self.calling_user,
            user_id=self.requested_user.id,
            account=None,
            agency=agency,
        )

    def test_get_user_internal(self):
        agency = magic_mixer.blend(core.models.Agency)
        test_helper.add_entity_permissions(self.calling_user, [Permission.READ, Permission.USER], None)
        test_helper.add_entity_permissions(self.requested_user, [Permission.READ], None)

        user_from_method = get_user(self.calling_user, self.requested_user.id, None, agency)
        self.assertEqual(user_from_method, self.requested_user)

    def test_get_user_internal_no_account_or_agency(self):
        test_helper.add_entity_permissions(self.calling_user, [Permission.READ, Permission.USER], None)
        test_helper.add_entity_permissions(self.requested_user, [Permission.READ], None)

        user_from_method = get_user(self.calling_user, self.requested_user.id, None, None)
        self.assertEqual(user_from_method, self.requested_user)

    def test_get_user_internal_no_access(self):
        agency = magic_mixer.blend(core.models.Agency)
        test_helper.add_entity_permissions(self.calling_user, [Permission.READ, Permission.USER], agency)
        test_helper.add_entity_permissions(self.requested_user, [Permission.READ], None)

        self.assertRaises(
            utils.exc.MissingDataError,
            get_user,
            calling_user=self.calling_user,
            user_id=self.requested_user.id,
            account=None,
            agency=agency,
        )

    def test_get_user_no_account_or_agency(self):
        agency = magic_mixer.blend(core.models.Agency)
        test_helper.add_entity_permissions(self.calling_user, [Permission.READ, Permission.USER], agency)
        test_helper.add_entity_permissions(self.requested_user, [Permission.READ], agency)

        self.assertRaises(
            utils.exc.ValidationError,
            get_user,
            calling_user=self.calling_user,
            user_id=self.requested_user.id,
            account=None,
            agency=None,
        )


class ConversionPixelAccessTestCase(ObjectAccessTestCaseMixin, TestCase):
    def test_get_conversion_pixel(self):
        account: core.models.Account = magic_mixer.blend(core.models.Account)
        pixel: core.models.ConversionPixel = magic_mixer.blend(core.models.ConversionPixel, account=account)
        user: zemauth.models.User = magic_mixer.blend_user()

        for permission in zemauth.features.entity_permission.Permission.get_all():
            self._for_all_entities(user, permission, entity_access.get_conversion_pixel, pixel)
            self._for_account(user, permission, entity_access.get_conversion_pixel, account, pixel, False)
            self._for_none(user, permission, entity_access.get_conversion_pixel, pixel)


class CreativeAccessTestCase(ObjectAccessTestCaseMixin, TestCase):
    def test_get_creative(self):
        agency: core.models.Agency = magic_mixer.blend(core.models.Agency)
        account: core.models.Account = magic_mixer.blend(core.models.Account, agency=agency)
        creative_with_agency_scope: core.features.creatives.Creative = magic_mixer.blend(
            core.features.creatives.Creative, agency=agency
        )
        creative_with_account_scope: core.features.creatives.Creative = magic_mixer.blend(
            core.features.creatives.Creative, account=account
        )
        user: zemauth.models.User = magic_mixer.blend_user()

        for permission in zemauth.features.entity_permission.Permission.get_all():
            self._for_all_entities(user, permission, entity_access.get_creative, creative_with_agency_scope)
            self._for_agency(user, permission, entity_access.get_creative, agency, creative_with_agency_scope)
            self._for_account(user, permission, entity_access.get_creative, account, creative_with_agency_scope, True)
            self._for_none(user, permission, entity_access.get_creative, creative_with_agency_scope)

            self._for_all_entities(user, permission, entity_access.get_creative, creative_with_account_scope)
            self._for_agency(user, permission, entity_access.get_creative, agency, creative_with_account_scope)
            self._for_account(user, permission, entity_access.get_creative, account, creative_with_account_scope, False)
            self._for_none(user, permission, entity_access.get_creative, creative_with_account_scope)
