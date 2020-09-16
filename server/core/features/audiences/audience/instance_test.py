import mock

import core.features.audiences
import core.models
import dash.constants
from utils.base_test_case import FutureBaseTestCase
from utils.magic_mixer import get_request_mock
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission


class InstanceTestCase(FutureBaseTestCase):
    def setUp(self):
        super().setUp()
        self.request = get_request_mock(self.user)

    @mock.patch("utils.redirector_helper.upsert_audience")
    @mock.patch("utils.k1_helper.update_account")
    @mock.patch("core.features.audiences.Audience.add_to_history")
    def test_create(self, history_mock, k1_update_account_mock, redirector_audience_mock):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account)
        audience = core.features.audiences.Audience.objects.create(
            self.request,
            "test",
            pixel,
            10,
            20,
            [{"type": dash.constants.AudienceRuleType.STARTS_WITH, "value": " http://test.com,  https://test2.com   "}],
        )
        self.assertEqual("test", audience.name)
        self.assertEqual(pixel, audience.pixel)
        self.assertFalse(audience.archived)
        self.assertEqual(10, audience.ttl)
        self.assertEqual(10, audience.prefill_days)
        rules = core.features.audiences.AudienceRule.objects.filter(audience=audience)
        self.assertEqual(1, rules.count())
        self.assertEqual("http://test.com,https://test2.com", rules[0].value)

        history_mock.assert_called_once()
        k1_update_account_mock.assert_called_once()
        redirector_audience_mock.assert_called_once()

    @mock.patch("utils.redirector_helper.upsert_audience")
    @mock.patch("utils.k1_helper.update_account")
    @mock.patch("core.features.audiences.Audience.add_to_history")
    def test_update(self, history_mock, k1_update_account_mock, redirector_audience_mock):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account, name="pixel1")
        audience = core.features.audiences.Audience.objects.create(
            self.request, "test", pixel, 10, 20, [{"type": 2, "value": "test_rule"}]
        )
        pixel2 = magic_mixer.blend(core.models.ConversionPixel, account=account, name="pixel2")
        user2 = magic_mixer.blend_user()
        old_id = audience.id
        audience.update(
            self.request,
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
        self.assertEqual(self.request.user, audience.created_by)

        self.assertEqual(2, history_mock.call_count)
        self.assertEqual(2, k1_update_account_mock.call_count)
        self.assertEqual(2, redirector_audience_mock.call_count)

    def test_archived(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account, name="pixel1")
        audience = core.features.audiences.Audience.objects.create(
            self.request, "test", pixel, 10, 20, [{"type": 2, "value": "test_rule"}]
        )
        self.assertFalse(audience.archived)
        audience.update(self.request, archived=True)
        self.assertTrue(audience.archived)
        audience.update(self.request, archived=False)
        self.assertFalse(audience.archived)
