import automation.rules
import utils.exc
from utils.base_test_case import BaseTestCase
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission

from . import serializers


class RulesSerializerTestCase(BaseTestCase):
    def test_without_agency_id_internal(self):
        request = magic_mixer.blend_request_user()
        rule = magic_mixer.blend(automation.rules.Rule)
        serializer = serializers.RuleSerializer(
            data={"id": rule.id, "name": "bla"}, partial=True, context={"request": request}
        )
        self.assertTrue(serializer.is_valid())
        self.assertFalse("agency" in serializer.validated_data)

    def test_agency_id_null_internal(self):
        request = magic_mixer.blend_request_user()
        rule = magic_mixer.blend(automation.rules.Rule)
        serializer = serializers.RuleSerializer(
            data={"id": rule.id, "agency_id": None}, partial=True, context={"request": request}
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["agency"], None)

    def test_agency_id_valid_internal(self):
        request = magic_mixer.blend_request_user()
        agency = self.mix_agency(request.user, permissions=[Permission.READ, Permission.WRITE])
        rule = magic_mixer.blend(automation.rules.Rule, agency=agency)
        serializer = serializers.RuleSerializer(
            data={"id": rule.id, "agency_id": agency.id}, partial=True, context={"request": request}
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["agency"], agency)

    def test_agency_id_invalid_internal(self):
        request = magic_mixer.blend_request_user()
        agency_without_user_permission = self.mix_agency(permissions=[Permission.READ, Permission.WRITE])
        rule = magic_mixer.blend(automation.rules.Rule, agency=agency_without_user_permission)
        serializer = serializers.RuleSerializer(
            data={"id": rule.id, "agency_id": agency_without_user_permission.id},
            partial=True,
            context={"request": request},
        )
        with self.assertRaises(utils.exc.MissingDataError):
            serializer.is_valid()

    def test_without_account_id_internal(self):
        request = magic_mixer.blend_request_user()
        rule = magic_mixer.blend(automation.rules.Rule)
        serializer = serializers.RuleSerializer(
            data={"id": rule.id, "name": "bla"}, partial=True, context={"request": request}
        )
        self.assertTrue(serializer.is_valid())
        self.assertFalse("account" in serializer.validated_data)

    def test_account_id_null_internal(self):
        request = magic_mixer.blend_request_user()
        rule = magic_mixer.blend(automation.rules.Rule)
        serializer = serializers.RuleSerializer(
            data={"id": rule.id, "account_id": None}, partial=True, context={"request": request}
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["account"], None)

    def test_account_id_valid_internal(self):
        request = magic_mixer.blend_request_user()
        account = self.mix_account(request.user, permissions=[Permission.READ, Permission.WRITE])
        rule = magic_mixer.blend(automation.rules.Rule, account=account)
        serializer = serializers.RuleSerializer(
            data={"id": rule.id, "account_id": account.id}, partial=True, context={"request": request}
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["account"], account)

    def test_account_id_invalid_internal(self):
        request = magic_mixer.blend_request_user()
        account_without_user_permission = self.mix_account(permissions=[Permission.READ, Permission.WRITE])
        rule = magic_mixer.blend(automation.rules.Rule, account=account_without_user_permission)
        serializer = serializers.RuleSerializer(
            data={"id": rule.id, "account_id": account_without_user_permission.id},
            partial=True,
            context={"request": request},
        )
        with self.assertRaises(utils.exc.MissingDataError):
            serializer.is_valid()
