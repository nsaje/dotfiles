import mock
from django.test import TestCase

import core.features.publisher_groups.publisher_group
import core.models
import dash.constants
import dash.history_helpers
from utils.magic_mixer import magic_mixer


class AdGroupInstanceTest(TestCase):
    def test_history_ad_group_created(self):
        request = magic_mixer.blend_request_user()
        ad_group = magic_mixer.blend(core.models.AdGroup)
        magic_mixer.cycle(5).blend(core.models.AdGroupSource, ad_group=ad_group)

        ad_group.write_history_created(request)

        history = dash.history_helpers.get_ad_group_history(ad_group)

        self.assertEqual(len(history), 7)
        self.assertRegex(
            history.first().changes_text, r"Created settings and automatically created campaigns for 5 sources .*"
        )

    def test_archive_restore(self):
        request = magic_mixer.blend_request_user()
        ad_group = magic_mixer.blend(core.models.AdGroup)
        ad_group.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.ACTIVE)
        self.assertFalse(ad_group.archived)
        self.assertFalse(ad_group.settings.archived)
        self.assertEqual(dash.constants.AdGroupSettingsState.ACTIVE, ad_group.settings.state)
        ad_group.archive(request)
        self.assertTrue(ad_group.archived)
        self.assertTrue(ad_group.settings.archived)
        self.assertEqual(dash.constants.AdGroupSettingsState.INACTIVE, ad_group.settings.state)
        ad_group.restore(request)
        self.assertFalse(ad_group.archived)
        self.assertFalse(ad_group.settings.archived)
        self.assertEqual(dash.constants.AdGroupSettingsState.INACTIVE, ad_group.settings.state)

    @mock.patch("utils.k1_helper.update_ad_group")
    def test_update_set_fields(self, mock_k1_ping):
        request = magic_mixer.blend_request_user(permissions=["fea_can_use_cpm_buying"])
        campaign = magic_mixer.blend(core.models.Campaign)
        ad_group = magic_mixer.blend(
            core.models.AdGroup,
            name="old_name",
            bidding_type=dash.constants.BiddingType.CPC,
            campaign=campaign,
            amplify_review=False,
        )
        blacklist = magic_mixer.blend(core.features.publisher_groups.publisher_group.PublisherGroup)
        whitelist = magic_mixer.blend(core.features.publisher_groups.publisher_group.PublisherGroup)
        tags = magic_mixer.cycle(2).blend(core.models.EntityTag)

        ad_group.update(
            request,
            name="new_name",
            bidding_type=dash.constants.BiddingType.CPM,
            archived=True,
            default_whitelist=whitelist,
            default_blacklist=blacklist,
            custom_flags={"cf1": True},
            entity_tags=tags,
        )
        self.assertEqual(ad_group.name, "new_name")
        self.assertEqual(ad_group.bidding_type, dash.constants.BiddingType.CPM)
        self.assertTrue(ad_group.archived)
        self.assertEqual(ad_group.default_whitelist, whitelist)
        self.assertEqual(ad_group.default_blacklist, blacklist)
        self.assertEqual(set(ad_group.entity_tags.all()), set(tags))
        mock_k1_ping.assert_has_calls([mock.call(ad_group, "Adgroup.update")])

    @mock.patch("utils.k1_helper.update_ad_group")
    def test_update_unset_fields(self, mock_k1_ping):
        request = magic_mixer.blend_request_user(permissions=["fea_can_use_cpm_buying"])
        campaign = magic_mixer.blend(core.models.Campaign)
        ad_group = magic_mixer.blend(
            core.models.AdGroup,
            name="old_name",
            bidding_type=dash.constants.BiddingType.CPM,
            campaign=campaign,
            amplify_review=False,
        )
        ad_group.update(
            request,
            bidding_type=dash.constants.BiddingType.CPC,
            archived=False,
            default_whitelist=None,
            default_blacklist=None,
            custom_flags={},
            amplify_review=False,
            entity_tags=[],
        )
        self.assertEqual(ad_group.bidding_type, dash.constants.BiddingType.CPC)
        self.assertFalse(ad_group.archived)
        self.assertIsNone(ad_group.default_whitelist)
        self.assertIsNone(ad_group.default_blacklist)
        self.assertEqual(list(ad_group.entity_tags.all()), [])
        self.assertFalse(ad_group.amplify_review)
        mock_k1_ping.assert_called_once_with(ad_group, "Adgroup.update")

    @mock.patch("utils.k1_helper.update_ad_group")
    def test_amplify_review_update(self, mock_k1_ping):
        request = magic_mixer.blend_request_user(permissions=["fea_can_use_cpm_buying"])
        campaign = magic_mixer.blend(core.models.Campaign)
        source_type_outbrain = core.models.SourceType.objects.create(type=dash.constants.SourceType.OUTBRAIN)
        outbrain_source = magic_mixer.blend(core.models.Source, source_type=source_type_outbrain)
        source_credentials = magic_mixer.blend(core.models.SourceCredentials)
        magic_mixer.blend(
            core.models.default_source_settings.DefaultSourceSettings,
            source=outbrain_source,
            credentials=source_credentials,
        )
        ad_group = magic_mixer.blend(core.models.AdGroup, name="name", campaign=campaign, amplify_review=None)

        ad_group.update(request, amplify_review=False)
        self.assertFalse(ad_group.amplify_review)
        mock_k1_ping.assert_called_once_with(ad_group, "Adgroup.update")
        self.assertFalse(core.models.AdGroupSource.objects.filter(ad_group=ad_group).exists())

        ad_group.update(request, amplify_review=True)
        self.assertTrue(ad_group.amplify_review)
        mock_k1_ping.assert_called_with(ad_group, "Adgroup.update")
        self.assertTrue(core.models.AdGroupSource.objects.filter(ad_group=ad_group, source=outbrain_source).exists())
