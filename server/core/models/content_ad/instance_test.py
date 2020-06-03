import mock
from django.conf import settings
from django.test import TestCase

import core.models.content_ad_source.model
import core.models.image_asset
from dash import constants
from utils import email_helper
from utils import exc
from utils import k1_helper
from utils import redirector_helper
from utils.magic_mixer import magic_mixer

from . import instance
from . import model


@mock.patch("django.conf.settings.HARDCODED_ACCOUNT_ID_OEN", 305)
class InstanceTest(TestCase):
    @mock.patch.object(redirector_helper, "update_redirect")
    @mock.patch.object(email_helper, "send_ad_group_notification_email")
    @mock.patch.object(k1_helper, "update_content_ad")
    def test_update(self, mock_k1_update, mock_email_helper, mock_update_redirect):
        content_ad = magic_mixer.blend(model.ContentAd)
        content_ad.ad_group.write_history = mock.MagicMock()

        updates = {field: field for field in instance.VALID_UPDATE_FIELDS}
        updates["tracker_urls"] = ["test1", "test2"]
        updates["image_width"] = 300
        updates["image_height"] = 250
        updates["icon"] = magic_mixer.blend(core.models.image_asset.ImageAsset)
        updates["document_id"] = 123
        updates["type"] = constants.AdType.CONTENT
        updates["url"] = "https://example.com"
        updates["state"] = constants.ContentAdSourceState.INACTIVE
        updates["archived"] = True
        content_ad.update(None, **updates)

        for field in updates:
            self.assertEqual(updates[field], getattr(content_ad, field))

        content_ad.ad_group.write_history.assert_called_with(
            "Content ad %s edited." % content_ad.pk, action_type=constants.HistoryActionType.CONTENT_AD_EDIT, user=None
        )

        content_ad.ad_group.write_history.has_calls(
            [
                mock.call(
                    "Content ad %s url set to https://example.com." % content_ad.pk,
                    action_type=constants.HistoryActionType.CONTENT_AD_EDIT,
                    user=None,
                ),
                mock.call(
                    "Content ad %s set to Enabled." % content_ad.pk,
                    action_type=constants.HistoryActionType.CONTENT_AD_STATE_CHANGE,
                    user=None,
                ),
                mock.call(
                    "Content ad %s set to Enabled." % content_ad.pk,
                    action_type=constants.HistoryActionType.CONTENT_AD_STATE_CHANGE,
                    user=None,
                ),
            ]
        )
        mock_k1_update.assert_has_calls(
            [mock.call(content_ad, msg="ContentAd.set_state"), mock.call(content_ad, msg="ContentAd.update")]
        )
        # (tfischer): email_helper should not be called when passing user=None
        mock_email_helper.assert_not_called()
        mock_update_redirect.assert_called_with("https://example.com", content_ad.redirect_id)

    @mock.patch.object(k1_helper, "update_content_ad")
    def test_oen_document_data(self, mock_k1_update):
        content_ad = magic_mixer.blend(
            model.ContentAd, ad_group__campaign__account__id=settings.HARDCODED_ACCOUNT_ID_OEN
        )

        additional_data = {
            "document_id": 12345,
            "language": "EN",
            "document_features": [{"value": "1234", "confidence": 0.99}, {"value": "4321", "confidence": 0.01}],
            "domain": "zemanta.com",
        }
        content_ad.update(None, additional_data=additional_data)
        self.assertEqual(content_ad.document_id, 12345)
        self.assertEqual(
            content_ad.document_features,
            {
                "language": [{"value": "en", "confidence": 1.0}],
                "categories": [{"value": "1234", "confidence": 0.99}, {"value": "4321", "confidence": 0.01}],
                "domain": "zemanta.com",
            },
        )

    @mock.patch.object(k1_helper, "update_content_ad")
    def test_oen_document_data_change_only_features(self, mock_k1_update):
        content_ad = magic_mixer.blend(
            model.ContentAd, ad_group__campaign__account__id=settings.HARDCODED_ACCOUNT_ID_OEN, document_id=12345
        )

        additional_data = {
            "document_id": 12345,
            "language": "EN",
            "document_features": [{"value": "1234", "confidence": 0.99}, {"value": "4321", "confidence": 0.01}],
            "domain": "zemanta.com",
        }
        content_ad.update(None, additional_data=additional_data)
        self.assertEqual(content_ad.document_id, 12345)
        self.assertEqual(
            content_ad.document_features,
            {
                "language": [{"value": "en", "confidence": 1.0}],
                "categories": [{"value": "1234", "confidence": 0.99}, {"value": "4321", "confidence": 0.01}],
                "domain": "zemanta.com",
            },
        )

    @mock.patch.object(k1_helper, "update_content_ad")
    def test_oen_document_data_no_change_if_fields_not_present(self, mock_k1_update):
        content_ad = magic_mixer.blend(model.ContentAd, document_id=123, document_features={"a": "b"})

        additional_data = {"my": "data"}
        content_ad.update(None, additional_data=additional_data)
        self.assertEqual(content_ad.document_id, 123)
        self.assertEqual(content_ad.document_features, {"a": "b"})

    @mock.patch.object(k1_helper, "update_content_ad")
    def test_oen_document_data_no_change_if_additional_data_not_present(self, mock_k1_update):
        content_ad = magic_mixer.blend(model.ContentAd, state=1, document_id=123, document_features={"a": "b"})

        content_ad.update(None, state=2, additional_data=None)
        self.assertEqual(content_ad.document_id, 123)
        self.assertEqual(content_ad.document_features, {"a": "b"})

    @mock.patch.object(core.models.AdGroup, "is_archived", return_value=True)
    def test_update_ad_group_archived_fail(self, mock_adgroup_is_archived):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        content_ad = magic_mixer.blend(core.models.ContentAd, ad_group=ad_group)
        with self.assertRaises(exc.ForbiddenError):
            content_ad.update(None, label="new label")

    def test_update_archived_content_ad_fail(self):
        content_ad = magic_mixer.blend(core.models.ContentAd, archived=True)
        with self.assertRaises(exc.ForbiddenError):
            content_ad.update(None, label="new label")
