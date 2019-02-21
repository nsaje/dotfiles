import mock
from django.test import TestCase

import core.models
from utils.magic_mixer import magic_mixer


class InstanceTestCase(TestCase):
    @mock.patch("utils.redirector_helper.upsert_audience")
    @mock.patch("utils.k1_helper.update_account")
    @mock.patch("core.models.Account.write_history")
    @mock.patch("utils.redirector_helper.update_pixel")
    def test_create(self, redirector_pixel_mock, history_mock, k1_update_account_mock, redirector_audience_mock):
        account = magic_mixer.blend(core.models.Account)
        pixel = core.models.ConversionPixel.objects.create(None, account, name="test", skip_notification=True)
        self.assertEqual("test", pixel.name)
        self.assertEqual(account, pixel.account)
        self.assertEqual(str(pixel.id), pixel.slug)
        self.assertFalse(pixel.audience_enabled)
        self.assertFalse(pixel.additional_pixel)

        pixel = core.models.ConversionPixel.objects.create(
            None, account, name="test2", slug="test_slug", skip_notification=True
        )
        self.assertEqual(str(pixel.id), pixel.slug)

        redirector_pixel_mock.assert_not_called()
        self.assertEqual(3, history_mock.call_count)
        k1_update_account_mock.assert_not_called()
        redirector_audience_mock.assert_not_called()

    @mock.patch("utils.redirector_helper.upsert_audience")
    @mock.patch("utils.k1_helper.update_account")
    @mock.patch("core.models.Account.write_history")
    @mock.patch("utils.redirector_helper.update_pixel")
    def test_update(self, redirector_pixel_mock, history_mock, k1_update_account_mock, redirector_audience_mock):
        request = magic_mixer.blend_request_user(
            permissions=[
                "archive_restore_entity",
                "can_promote_additional_pixel",
                "can_redirect_pixels",
                "can_see_pixel_notes",
            ]
        )
        account = magic_mixer.blend(core.models.Account)
        core.models.ConversionPixel.objects.create(request, account, name="test_audience", audience_enabled=True)
        pixel = core.models.ConversionPixel.objects.create(request, account, name="test")
        core.features.audiences.Audience.objects.create(request, "test_audience", pixel, 0, 0, [])
        account2 = magic_mixer.blend(core.models.Account)
        old_id = pixel.id
        pixel.update(
            request,
            id=old_id + 1000,
            account=account2,
            name="test2",
            slug="test_slug",
            additional_pixel=True,
            redirect_url="test_url",
            notes="test_notes",
            last_triggered="2018-01-01",
            impressions=1000,
            last_sync_dt="2018-01-01",
            created_dt="2018-01-01",
        )
        self.assertEqual(old_id, pixel.id)
        self.assertEqual(account, pixel.account)
        self.assertEqual("test2", pixel.name)
        self.assertEqual(str(pixel.id), pixel.slug)
        self.assertTrue(pixel.additional_pixel)
        self.assertEqual("test_url", pixel.redirect_url)
        self.assertEqual("test_notes", pixel.notes)
        self.assertNotEqual("2018-01-01", pixel.last_triggered)
        self.assertNotEqual(1000, pixel.impressions)
        self.assertNotEqual("2018-01-01", pixel.last_sync_dt)
        self.assertNotEqual("2018-01-01", pixel.created_dt)

        redirector_pixel_mock.assert_called_once()
        self.assertEqual(8, history_mock.call_count)
        self.assertEqual(3, k1_update_account_mock.call_count)
        self.assertEqual(2, redirector_audience_mock.call_count)

    def test_archived(self):
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(core.models.Account)
        pixel = core.models.ConversionPixel.objects.create(request, account, name="test", skip_notification=True)
        pixel.update(request, archived=True)
        self.assertFalse(pixel.archived)

        request = magic_mixer.blend_request_user(permissions=["archive_restore_entity"])
        pixel.update(request, archived=True)
        self.assertTrue(pixel.archived)

    @mock.patch("utils.redirector_helper.upsert_audience")
    @mock.patch("utils.k1_helper.update_account")
    @mock.patch("core.models.Account.write_history")
    @mock.patch("utils.redirector_helper.update_pixel")
    def test_permissioned_fields(
        self, redirector_pixel_mock, history_mock, k1_update_account_mock, redirector_audience_mock
    ):
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(core.models.Account)
        core.models.ConversionPixel.objects.create(request, account, name="test_audience", audience_enabled=True)
        pixel = core.models.ConversionPixel.objects.create(request, account, name="test")
        core.features.audiences.Audience.objects.create(request, "test_audience", pixel, 0, 0, [])
        pixel.update(request, additional_pixel=True, redirect_url="test_url", notes="test_notes")
        self.assertFalse(pixel.additional_pixel)
        self.assertNotEqual("test_url", pixel.redirect_url)
        self.assertNotEqual("test_notes", pixel.notes)

        redirector_pixel_mock.assert_not_called()
        self.assertEqual(4, history_mock.call_count)
        self.assertEqual(2, k1_update_account_mock.call_count)
        redirector_audience_mock.assert_called_once()

        request = magic_mixer.blend_request_user(
            permissions=[
                "archive_restore_entity",
                "can_promote_additional_pixel",
                "can_redirect_pixels",
                "can_see_pixel_notes",
            ]
        )
        pixel.update(request, additional_pixel=True, redirect_url="test_url", notes="test_notes")
        self.assertTrue(pixel.additional_pixel)
        self.assertEqual("test_url", pixel.redirect_url)
        self.assertEqual("test_notes", pixel.notes)

        redirector_pixel_mock.assert_called_once()
        self.assertEqual(6, history_mock.call_count)
        self.assertEqual(3, k1_update_account_mock.call_count)
        self.assertEqual(2, redirector_audience_mock.call_count)
