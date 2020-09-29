import mock
from django.test import TestCase

import core.models
from utils.magic_mixer import magic_mixer

from . import exceptions


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

        pixel = core.models.ConversionPixel.objects.create(
            None, account, name="test2", slug="test_slug", skip_notification=True
        )
        self.assertEqual(str(pixel.id), pixel.slug)

        self.assertEqual(2, redirector_pixel_mock.call_count)
        self.assertEqual(3, history_mock.call_count)
        k1_update_account_mock.assert_not_called()
        redirector_audience_mock.assert_not_called()

    @mock.patch("utils.redirector_helper.upsert_audience")
    @mock.patch("utils.k1_helper.update_account")
    @mock.patch("core.models.Account.write_history")
    @mock.patch("utils.redirector_helper.update_pixel")
    def test_update(self, redirector_pixel_mock, history_mock, k1_update_account_mock, redirector_audience_mock):
        request = magic_mixer.blend_request_user(permissions=["can_redirect_pixels"])
        account = magic_mixer.blend(core.models.Account)
        core.models.ConversionPixel.objects.create(request, account, name="test_audience")
        pixel = core.models.ConversionPixel.objects.create(request, account, name="test")
        core.features.audiences.Audience.objects.create(request, "test_audience", pixel, 0, 0, [])
        account2 = magic_mixer.blend(core.models.Account)
        old_id = pixel.id
        pixel.update(
            request,
            id=old_id + 1000,
            account=account2,
            slug="test_slug",
            redirect_url="test_url",
            notes="test_notes",
            last_triggered="2018-01-01",
            impressions=1000,
            last_sync_dt="2018-01-01",
            created_dt="2018-01-01",
        )
        self.assertEqual(old_id, pixel.id)
        self.assertEqual(account, pixel.account)
        self.assertEqual(str(pixel.id), pixel.slug)
        self.assertEqual("test_url", pixel.redirect_url)
        self.assertEqual("test_notes", pixel.notes)
        self.assertNotEqual("2018-01-01", pixel.last_triggered)
        self.assertNotEqual(1000, pixel.impressions)
        self.assertNotEqual("2018-01-01", pixel.last_sync_dt)
        self.assertNotEqual("2018-01-01", pixel.created_dt)

        self.assertEqual(3, redirector_pixel_mock.call_count)
        self.assertEqual(6, history_mock.call_count)
        self.assertEqual(2, k1_update_account_mock.call_count)
        self.assertEqual(2, redirector_audience_mock.call_count)

    @mock.patch("utils.redirector_helper.upsert_audience")
    @mock.patch("utils.k1_helper.update_account")
    @mock.patch("core.models.Account.write_history")
    @mock.patch("utils.redirector_helper.update_pixel")
    def test_update_name(self, redirector_pixel_mock, history_mock, k1_update_account_mock, redirector_audience_mock):
        request = magic_mixer.blend_request_user(permissions=["can_redirect_pixels"])
        account = magic_mixer.blend(core.models.Account)
        core.models.ConversionPixel.objects.create(request, account, name="test_audience")
        pixel = core.models.ConversionPixel.objects.create(request, account, name="test")
        core.features.audiences.Audience.objects.create(request, "test_audience", pixel, 0, 0, [])

        with self.assertRaises(exceptions.PixelNameNotEditable):
            pixel.update(request, name="test2")

    def test_archived(self):
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(core.models.Account)
        pixel = core.models.ConversionPixel.objects.create(request, account, name="test", skip_notification=True)
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
        core.models.ConversionPixel.objects.create(request, account, name="test_audience")
        pixel = core.models.ConversionPixel.objects.create(request, account, name="test")
        core.features.audiences.Audience.objects.create(request, "test_audience", pixel, 0, 0, [])
        pixel.update(request, redirect_url="test_url", notes="test_notes")
        self.assertNotEqual("test_url", pixel.redirect_url)

        self.assertEqual("test_notes", pixel.notes)
        self.assertEqual(2, redirector_pixel_mock.call_count)
        self.assertEqual(4, history_mock.call_count)
        self.assertEqual(2, k1_update_account_mock.call_count)
        self.assertEqual(2, redirector_audience_mock.call_count)

        request = magic_mixer.blend_request_user(permissions=["can_redirect_pixels"])
        pixel.update(request, redirect_url="test_url", notes="test_notes")
        self.assertEqual("test_url", pixel.redirect_url)
        self.assertEqual("test_notes", pixel.notes)

        self.assertEqual(3, redirector_pixel_mock.call_count)
        self.assertEqual(5, history_mock.call_count)
        self.assertEqual(3, k1_update_account_mock.call_count)
        self.assertEqual(3, redirector_audience_mock.call_count)
