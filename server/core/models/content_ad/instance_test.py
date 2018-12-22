import mock
from django.test import TestCase

import core.models.content_ad_source.model
from dash import constants
from utils import email_helper
from utils import k1_helper
from utils import redirector_helper
from utils.magic_mixer import magic_mixer

from . import instance
from . import model


class InstanceTest(TestCase):
    @mock.patch.object(email_helper, "send_ad_group_notification_email")
    @mock.patch.object(k1_helper, "update_content_ad")
    def test_set_state(self, mock_k1_update, mock_email_helper):
        content_ad = magic_mixer.blend(model.ContentAd, state=constants.ContentAdSourceState.INACTIVE)
        magic_mixer.cycle(10).blend(
            core.models.content_ad_source.model.ContentAdSource,
            content_ad=content_ad,
            state=constants.ContentAdSourceState.INACTIVE,
        )
        content_ad.ad_group.write_history = mock.MagicMock()

        content_ad.set_state(None, constants.ContentAdSourceState.ACTIVE)
        self.assertEqual(constants.ContentAdSourceState.ACTIVE, content_ad.state)
        for cas in content_ad.contentadsource_set.all():
            self.assertEqual(constants.ContentAdSourceState.ACTIVE, cas.state)
        content_ad.ad_group.write_history.assert_called_with(
            "Content ad %s set to Enabled." % content_ad.pk,
            action_type=constants.HistoryActionType.CONTENT_AD_STATE_CHANGE,
            user=None,
        )
        mock_k1_update.assert_called_with(content_ad, msg=mock.ANY)
        mock_email_helper.assert_called_once()

    @mock.patch.object(redirector_helper, "update_redirect")
    def test_set_url(self, mock_update_redirect):
        content_ad = magic_mixer.blend(model.ContentAd, url="http://what.com")
        content_ad.ad_group.write_history = mock.MagicMock()

        content_ad.set_url(None, "https://example.com")
        self.assertEqual("https://example.com", content_ad.url)
        content_ad.ad_group.write_history.assert_called_with(
            "Content ad %s url set to https://example.com." % content_ad.pk,
            action_type=constants.HistoryActionType.CONTENT_AD_EDIT,
            user=None,
        )
        mock_update_redirect.assert_called_with("https://example.com", content_ad.redirect_id)

    @mock.patch.object(k1_helper, "update_content_ad")
    def test_update(self, mock_k1_update):
        content_ad = magic_mixer.blend(model.ContentAd)
        content_ad.ad_group.write_history = mock.MagicMock()

        updates = {field: field for field in instance.VALID_UPDATE_FIELDS}
        updates["tracker_urls"] = ["test1", "test2"]
        updates["image_width"] = 300
        updates["image_height"] = 250
        updates["type"] = constants.AdType.CONTENT
        content_ad.update(None, **updates)

        for field in updates:
            self.assertEqual(updates[field], getattr(content_ad, field))

        content_ad.ad_group.write_history.assert_called_with(
            "Content ad %s edited." % content_ad.pk, action_type=constants.HistoryActionType.CONTENT_AD_EDIT, user=None
        )
        mock_k1_update.assert_called_with(content_ad, msg=mock.ANY)

    @mock.patch.object(k1_helper, "update_content_ad")
    def test_oen_document_data(self, mock_k1_update):
        content_ad = magic_mixer.blend(model.ContentAd, ad_group__campaign__account__id=305)

        additional_data = {
            "document_id": 12345,
            "language": "EN",
            "document_features": [{"value": "1234", "confidence": 0.99}, {"value": "4321", "confidence": 0.01}],
        }
        content_ad.update(None, additional_data=additional_data)
        self.assertEqual(content_ad.document_id, 12345)
        self.assertEqual(
            content_ad.document_features,
            {
                "language": [{"value": "en", "confidence": 1.0}],
                "categories": [{"value": "1234", "confidence": 0.99}, {"value": "4321", "confidence": 0.01}],
            },
        )

    @mock.patch.object(k1_helper, "update_content_ad")
    def test_oen_document_data_no_change_if_not_present(self, mock_k1_update):
        content_ad = magic_mixer.blend(model.ContentAd, document_id=123, document_features={"a": "b"})

        additional_data = {"language": "EN"}
        content_ad.update(None, additional_data=additional_data)
        self.assertEqual(content_ad.document_id, 123)
        self.assertEqual(content_ad.document_features, {"a": "b"})
