import mock
from django.test import TestCase

import dash.models
import utils.exc
from restapi import access
from utils.magic_mixer import magic_mixer


class GeneratePermissionClass(TestCase):
    def test_superuser(self):
        request = magic_mixer.blend_request_user(is_superuser=True)
        cls = access.gen_permission_class("zemauth.can_set_advanced_device_targeting")
        self.assertTrue(cls().has_permission(request, mock.Mock()))

    def test_single_permission(self):
        request = magic_mixer.blend_request_user(["can_set_advanced_device_targeting"])
        cls = access.gen_permission_class("zemauth.can_set_advanced_device_targeting")
        self.assertTrue(cls().has_permission(request, mock.Mock()))

        cls = access.gen_permission_class("zemauth.fea_new_geo_targeting")
        self.assertFalse(cls().has_permission(request, mock.Mock()))

    def test_multi_access(self):
        request = magic_mixer.blend_request_user(["can_set_advanced_device_targeting", "fea_new_geo_targeting"])
        # must have all access
        cls = access.gen_permission_class("zemauth.fea_new_geo_targeting", "zemauth.can_set_advanced_device_targeting")
        self.assertTrue(cls().has_permission(request, mock.Mock()))

        request = magic_mixer.blend_request_user(["can_set_advanced_device_targeting"])
        self.assertFalse(cls().has_permission(request, mock.Mock()))

        request = magic_mixer.blend_request_user(["fea_new_geo_targeting"])
        self.assertFalse(cls().has_permission(request, mock.Mock()))


class ObjectAccess(TestCase):
    def test_has_account_access(self):
        request = magic_mixer.blend_request_user()
        cls = access.HasAccountAccess

        # linked to user
        account = magic_mixer.blend(dash.models.Account, users=request.user)
        self.assertTrue(cls().has_permission(request, mock.Mock(kwargs={"account_id": account.id})))

        # no link
        account = magic_mixer.blend(dash.models.Account)
        with self.assertRaises(utils.exc.MissingDataError):
            cls().has_permission(request, mock.Mock(kwargs={"account_id": account.id}))

    def test_has_campaign_access(self):
        request = magic_mixer.blend_request_user()
        cls = access.HasCampaignAccess

        # linked to user
        campaign = magic_mixer.blend(dash.models.Campaign, account__users=request.user)
        self.assertTrue(cls().has_permission(request, mock.Mock(kwargs={"campaign_id": campaign.id})))

        # no link
        campaign = magic_mixer.blend(dash.models.Campaign)
        with self.assertRaises(utils.exc.MissingDataError):
            cls().has_permission(request, mock.Mock(kwargs={"campaign_id": campaign.id}))

    def test_has_adgroup_access(self):
        request = magic_mixer.blend_request_user()
        cls = access.HasAdGroupAccess

        # linked to user
        ad_group = magic_mixer.blend(dash.models.AdGroup, campaign__account__users=request.user)
        self.assertTrue(cls().has_permission(request, mock.Mock(kwargs={"ad_group_id": ad_group.id})))

        # no link
        ad_group = magic_mixer.blend(dash.models.AdGroup)
        with self.assertRaises(utils.exc.MissingDataError):
            cls().has_permission(request, mock.Mock(kwargs={"ad_group_id": ad_group.id}))
