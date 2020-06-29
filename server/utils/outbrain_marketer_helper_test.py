from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.test import TestCase

import dash.models
from utils import outbrain_marketer_helper
from utils.magic_mixer import magic_mixer


class ParseMarketerNameTestCase(TestCase):
    def test_parse_marketer_name(self):
        account_id, marketer_version = outbrain_marketer_helper.parse_marketer_name("Zemanta_1234_5")
        self.assertEqual(account_id, 1234)
        self.assertEqual(marketer_version, 5)

    def test_parse_none(self):
        with self.assertRaisesMessage(ValueError, "Marketer name can not be None"):
            outbrain_marketer_helper.parse_marketer_name(None)

    def test_parse_empty(self):
        with self.assertRaisesMessage(ValueError, "Invalid Zemanta marketer name"):
            outbrain_marketer_helper.parse_marketer_name("")

    def test_parse_invalid(self):
        with self.assertRaisesMessage(ValueError, "Invalid Zemanta marketer name"):
            outbrain_marketer_helper.parse_marketer_name("invalid")

    def test_parse_non_numeric(self):
        with self.assertRaisesMessage(ValueError, "Invalid Zemanta marketer name"):
            outbrain_marketer_helper.parse_marketer_name("Zemanta_4a2_1b")

    def test_parse_missing_parts(self):
        with self.assertRaisesMessage(ValueError, "Invalid Zemanta marketer name"):
            outbrain_marketer_helper.parse_marketer_name("Zemanta_1234_")


class CalculateMarketerTypeTestCase(TestCase):
    def setUp(self):
        self.account = magic_mixer.blend(dash.models.Account)

    def test_one_mapped_account_type_tag(self):
        self.account.entity_tags.add(magic_mixer.blend(dash.models.EntityTag, name="account_type/audiencedev/socagg"))
        marketer_type, content_classification = outbrain_marketer_helper.calculate_marketer_parameters(self.account.id)
        self.assertEqual(marketer_type, "ELASTIC_PUBLISHER")
        self.assertEqual(content_classification, "PremiumElasticPublishers")

    def test_two_mapped_account_type_tags(self):
        self.account.entity_tags.add(
            magic_mixer.blend(dash.models.EntityTag, name="account_type/performance/search"),
            magic_mixer.blend(dash.models.EntityTag, name="account_type/audiencedev/socagg"),
        )
        marketer_type, content_classification = outbrain_marketer_helper.calculate_marketer_parameters(self.account.id)
        self.assertEqual(marketer_type, "ELASTIC_PUBLISHER")
        self.assertEqual(content_classification, "PremiumElasticPublishers")

    def test_no_account_type_tags(self):
        marketer_type, content_classification = outbrain_marketer_helper.calculate_marketer_parameters(self.account.id)
        self.assertEqual(marketer_type, outbrain_marketer_helper.DEFAULT_OUTBRAIN_MARKETER_TYPE)
        self.assertEqual(
            content_classification, outbrain_marketer_helper.DEFAULT_OUTBRAIN_MARKETER_CONTENT_CLASSIFICATION
        )

    def test_two_accounts_with_mapped_account_type_tags(self):
        account = magic_mixer.blend(dash.models.Account)
        account.entity_tags.add(magic_mixer.blend(dash.models.EntityTag, name="account_type/audiencedev/socagg"))
        self.account.entity_tags.add(magic_mixer.blend(dash.models.EntityTag, name="account_type/performance/search"))
        marketer_type, content_classification = outbrain_marketer_helper.calculate_marketer_parameters(self.account.id)
        self.assertEqual(marketer_type, "SEARCH")
        self.assertEqual(content_classification, "SERP")
        marketer_type, content_classification = outbrain_marketer_helper.calculate_marketer_parameters(account.id)
        self.assertEqual(marketer_type, "ELASTIC_PUBLISHER")
        self.assertEqual(content_classification, "PremiumElasticPublishers")

    def test_unmapped_account_type_tag(self):
        self.account.entity_tags.add(magic_mixer.blend(dash.models.EntityTag, name="account_type/unknown/tag"))
        marketer_type, content_classification = outbrain_marketer_helper.calculate_marketer_parameters(self.account.id)
        self.assertEqual(marketer_type, outbrain_marketer_helper.DEFAULT_OUTBRAIN_MARKETER_TYPE)
        self.assertEqual(
            content_classification, outbrain_marketer_helper.DEFAULT_OUTBRAIN_MARKETER_CONTENT_CLASSIFICATION
        )

    def test_non_account_type_tag(self):
        self.account.entity_tags.add(magic_mixer.blend(dash.models.EntityTag, name="invalid/tag"))
        marketer_type, content_classification = outbrain_marketer_helper.calculate_marketer_parameters(self.account.id)
        self.assertEqual(marketer_type, outbrain_marketer_helper.DEFAULT_OUTBRAIN_MARKETER_TYPE)
        self.assertEqual(
            content_classification, outbrain_marketer_helper.DEFAULT_OUTBRAIN_MARKETER_CONTENT_CLASSIFICATION
        )

    def test_one_mapped_one_non_account_type_tag(self):
        self.account.entity_tags.add(
            magic_mixer.blend(dash.models.EntityTag, name="invalild/tag"),
            magic_mixer.blend(dash.models.EntityTag, name="account_type/audiencedev/socagg"),
        )
        marketer_type, content_classification = outbrain_marketer_helper.calculate_marketer_parameters(self.account.id)
        self.assertEqual(marketer_type, "ELASTIC_PUBLISHER")
        self.assertEqual(content_classification, "PremiumElasticPublishers")


class GetMarketerUserEmailsTestCase(TestCase):
    def setUp(self):
        self.permission_codename = "campaign_settings_cs_rep"
        self.prodops_group = magic_mixer.blend(Group, name="ProdOps")
        self.prodops_group.permissions.add(Permission.objects.get(codename=self.permission_codename))
        self.non_cs_user_1 = magic_mixer.blend_user()
        self.non_cs_user_2 = magic_mixer.blend_user()
        self.cs_user_1 = magic_mixer.blend_user(permissions=[self.permission_codename])
        self.cs_user_2 = magic_mixer.blend_user(permissions=[self.permission_codename])
        self.prodops_user_1 = magic_mixer.blend_user()
        self.prodops_user_1.groups.add(self.prodops_group)
        self.prodops_user_2 = magic_mixer.blend_user()
        self.prodops_user_2.groups.add(self.prodops_group)

    def test_with_defaults(self):
        self.assertCountEqual(
            outbrain_marketer_helper.get_marketer_user_emails(),
            [self.cs_user_1.email, self.cs_user_2.email] + outbrain_marketer_helper.DEFUALT_OUTBRAIN_USER_EMAILS,
        )

    def test_without_defaults(self):
        self.assertCountEqual(
            outbrain_marketer_helper.get_marketer_user_emails(include_defaults=False),
            [self.cs_user_1.email, self.cs_user_2.email],
        )
