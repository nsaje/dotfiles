import mock
from django.test import TestCase

import core.features.audiences
import core.models
from utils.magic_mixer import magic_mixer


class InstanceTestCase(TestCase):
    @mock.patch("utils.redirector_helper.upsert_audience")
    @mock.patch("utils.k1_helper.update_account")
    @mock.patch("core.features.audiences.Audience.add_to_history")
    def test_create(self, history_mock, k1_update_account_mock, redirector_audience_mock):
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(core.models.Account, users=[request.user])
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account)
        audience = core.features.audiences.Audience.objects.create(
            request, "test", pixel, 10, 20, [{"type": 2, "value": "test_rule"}]
        )
        self.assertEqual("test", audience.name)
        self.assertEqual(pixel, audience.pixel)
        self.assertFalse(audience.archived)
        self.assertEqual(10, audience.ttl)
        self.assertEqual(10, audience.prefill_days)
        self.assertEqual(1, core.features.audiences.AudienceRule.objects.filter(audience=audience).count())

        history_mock.assert_called_once()
        k1_update_account_mock.assert_called_once()
        redirector_audience_mock.assert_called_once()

    @mock.patch("utils.redirector_helper.upsert_audience")
    @mock.patch("utils.k1_helper.update_account")
    @mock.patch("core.features.audiences.Audience.add_to_history")
    def test_update(self, history_mock, k1_update_account_mock, redirector_audience_mock):
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(core.models.Account, users=[request.user])
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account, name="pixel1")
        audience = core.features.audiences.Audience.objects.create(
            request, "test", pixel, 10, 20, [{"type": 2, "value": "test_rule"}]
        )
        pixel2 = magic_mixer.blend(core.models.ConversionPixel, account=account, name="pixel2")
        user2 = magic_mixer.blend_user()
        old_id = audience.id
        audience.update(
            request,
            id=old_id + 1000,
            name="test2",
            pixel=pixel2,
            ttl=100,
            prefill_days=1000,
            created_dt="2018-01-01",
            modified_dt="2018-01-01",
            created_by=user2,
        )
        self.assertEqual(old_id, audience.id)
        self.assertEqual("test2", audience.name)
        self.assertEqual(pixel, audience.pixel)
        self.assertFalse(audience.archived)
        self.assertEqual(10, audience.ttl)
        self.assertEqual(10, audience.prefill_days)
        self.assertNotEqual("2018-01-01", audience.created_dt)
        self.assertNotEqual("2018-01-01", audience.modified_dt)
        self.assertEqual(request.user, audience.created_by)

        self.assertEqual(2, history_mock.call_count)
        self.assertEqual(2, k1_update_account_mock.call_count)
        self.assertEqual(2, redirector_audience_mock.call_count)

    def test_archived(self):
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(core.models.Account, users=[request.user])
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account, name="pixel1")
        audience = core.features.audiences.Audience.objects.create(
            request, "test", pixel, 10, 20, [{"type": 2, "value": "test_rule"}]
        )
        self.assertFalse(audience.archived)
        audience.update(request, archived=True)
        self.assertTrue(audience.archived)
        audience.update(request, archived=False)
        self.assertFalse(audience.archived)
