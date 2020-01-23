from django.test import TestCase

import core.models
from dash import constants
from utils.magic_mixer import magic_mixer

from . import exceptions


class ValidationTestCase(TestCase):
    def test_bidding_type_new_ad_group(self):
        request = magic_mixer.blend_request_user(permissions=["fea_can_use_cpm_buying"])
        ad_group = magic_mixer.blend(
            core.models.AdGroup, bidding_type=constants.BiddingType.CPC, state=constants.AdGroupSettingsState.INACTIVE
        )
        ad_group.update(request, bidding_type=constants.BiddingType.CPM)
        self.assertEqual(ad_group.bidding_type, constants.BiddingType.CPM)

    def test_bidding_type_new_ad_group_no_request(self):
        ad_group = magic_mixer.blend(
            core.models.AdGroup, bidding_type=constants.BiddingType.CPC, state=constants.AdGroupSettingsState.INACTIVE
        )
        ad_group.update(None, bidding_type=constants.BiddingType.CPM)
        self.assertEqual(ad_group.bidding_type, constants.BiddingType.CPM)

    def test_bidding_type_new_ad_group_no_permission(self):
        request = magic_mixer.blend_request_user()
        ad_group = magic_mixer.blend(
            core.models.AdGroup, bidding_type=constants.BiddingType.CPC, state=constants.AdGroupSettingsState.INACTIVE
        )
        with self.assertRaises(exceptions.CannotChangeBiddingType):
            ad_group.update(request, bidding_type=constants.BiddingType.CPM)

    def test_bidding_type_turned_on_ad_group(self):
        request = magic_mixer.blend_request_user(permissions=["fea_can_use_cpm_buying"])
        ad_group = magic_mixer.blend(
            core.models.AdGroup, bidding_type=constants.BiddingType.CPC, state=constants.AdGroupSettingsState.INACTIVE
        )
        ad_group.settings.update_unsafe(request, state=constants.AdGroupRunningStatus.ACTIVE)
        ad_group.settings.update_unsafe(request, state=constants.AdGroupRunningStatus.INACTIVE)
        with self.assertRaises(exceptions.CannotChangeBiddingType):
            ad_group.update(request, bidding_type=constants.BiddingType.CPM)

    def test_bidding_type_turned_on_ad_group_no_request(self):
        ad_group = magic_mixer.blend(
            core.models.AdGroup, bidding_type=constants.BiddingType.CPC, state=constants.AdGroupSettingsState.INACTIVE
        )
        ad_group.settings.update_unsafe(None, state=constants.AdGroupRunningStatus.ACTIVE)
        ad_group.settings.update_unsafe(None, state=constants.AdGroupRunningStatus.INACTIVE)
        with self.assertRaises(exceptions.CannotChangeBiddingType):
            ad_group.update(None, bidding_type=constants.BiddingType.CPM)
