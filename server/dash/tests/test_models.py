import datetime
from decimal import Decimal

from django.db.models.signals import pre_save
from django.test import TestCase

from dash import models
from zemauth import models as zemauthmodels
from utils import exc


class AdGroupSettingsTest(TestCase):

    fixtures = ['test_models.yaml']

    def test_settings_fields(self):
        meta_fields = [
            'id',
            'ad_group',
            'ad_group_id',
            'created_dt',
            'created_by',
            'created_by_id',
            'changes_text'
        ]

        all_fields = set(models.AdGroupSettings._settings_fields + meta_fields)
        model_fields = set(models.AdGroupSettings._meta.get_all_field_names())

        self.assertEqual(model_fields, all_fields)

    def test_get_settings_dict(self):
        settings_dict = {
            'archived': False,
            'state': 1,
            'cpc_cc': Decimal('0.12'),
            'daily_budget_cc': Decimal('50'),
            'start_date': datetime.date(2014, 6, 4),
            'end_date': datetime.date(2014, 6, 5),
            'target_devices': u'',
            'tracking_code': u'',
            'target_regions': u'',
        }
        self.assertEqual(
            models.AdGroupSettings.objects.get(id=1).get_settings_dict(),
            settings_dict,
        )


def created_by_patch(sender, instance, **kwargs):
    u = zemauthmodels.User.objects.get(id=1)
    if instance.pk is not None:
        return

    instance.created_by = u


class ArchiveRestoreTestCase(TestCase):

    fixtures = ['test_models.yaml']

    def setUp(self):
        pre_save.connect(created_by_patch, sender=models.AdGroupSettings)
        pre_save.connect(created_by_patch, sender=models.CampaignSettings)
        pre_save.connect(created_by_patch, sender=models.AccountSettings)

    def tearDown(self):
        pre_save.disconnect(created_by_patch, sender=models.AdGroupSettings)
        pre_save.disconnect(created_by_patch, sender=models.CampaignSettings)
        pre_save.disconnect(created_by_patch, sender=models.AccountSettings)

    def test_archive_ad_group(self):
        ag1 = models.AdGroup.objects.get(id=1)
        ag2 = models.AdGroup.objects.get(id=2)

        self.assertFalse(ag1.get_current_settings().archived)
        self.assertFalse(ag2.get_current_settings().archived)

        self.assertFalse(ag1.can_archive())
        self.assertTrue(ag2.can_archive())

        with self.assertRaises(exc.ForbiddenError):
            ag1.archive()

        ag2.archive()
        self.assertTrue(ag2.get_current_settings().archived)

    def test_archive_campaign(self):
        c1 = models.Campaign.objects.get(id=1)
        c2 = models.Campaign.objects.get(id=2)

        self.assertFalse(c1.get_current_settings().archived)
        self.assertFalse(c2.get_current_settings().archived)

        self.assertFalse(c1.can_archive())
        self.assertTrue(c2.can_archive())

        with self.assertRaises(exc.ForbiddenError):
            c1.archive()

        c2.archive()
        self.assertTrue(c2.get_current_settings().archived)

        ag = c2.adgroup_set.all()[0]
        self.assertTrue(ag.get_current_settings().archived)

    def test_archive_account(self):
        a1 = models.Account.objects.get(id=1)
        a2 = models.Account.objects.get(id=2)

        self.assertFalse(a1.get_current_settings().archived)
        self.assertFalse(a2.get_current_settings().archived)

        self.assertFalse(a1.can_archive())
        self.assertTrue(a2.can_archive())

        with self.assertRaises(exc.ForbiddenError):
            a1.archive()

        a2.archive()
        self.assertTrue(a2.get_current_settings().archived)

        c = a2.campaign_set.all()[0]
        self.assertTrue(c.get_current_settings().archived)

        ag = c.adgroup_set.all()[0]
        self.assertTrue(ag.get_current_settings().archived)

    def test_restore_account(self):
        a = models.Account.objects.get(id=2)

        self.assertTrue(a.can_archive())
        a.archive()

        self.assertTrue(a.can_restore())
        a.restore()

        self.assertFalse(a.get_current_settings().archived)

        c = a.campaign_set.all()[0]
        self.assertTrue(c.get_current_settings().archived)

        ag = c.adgroup_set.all()[0]
        self.assertTrue(ag.get_current_settings().archived)

    def test_restore_campaign(self):
        c = models.Campaign.objects.get(id=2)

        self.assertTrue(c.can_archive())
        c.archive()

        self.assertTrue(c.can_restore())
        c.restore()

        self.assertFalse(c.get_current_settings().archived)

        ag = c.adgroup_set.all()[0]
        self.assertTrue(ag.get_current_settings().archived)

    def test_restore_ad_group(self):
        ag = models.AdGroup.objects.get(id=2)

        self.assertTrue(ag.can_archive())
        ag.archive()

        self.assertTrue(ag.can_restore())
        ag.restore()

        self.assertFalse(ag.get_current_settings().archived)

    def test_restore_campaign_fail(self):
        a = models.Account.objects.get(id=2)

        a.archive()

        c = a.campaign_set.all()[0]
        self.assertTrue(c.get_current_settings().archived)
        self.assertFalse(c.can_restore())

        with self.assertRaises(exc.ForbiddenError):
            c.restore()

        a.restore()
        self.assertTrue(c.get_current_settings().archived)
        self.assertTrue(c.can_restore())

        c.restore()
        self.assertFalse(c.get_current_settings().archived)

    def test_restore_ad_group_fail(self):
        c = models.Campaign.objects.get(id=2)

        c.archive()

        ag = c.adgroup_set.all()[0]
        self.assertTrue(ag.get_current_settings().archived)
        self.assertFalse(ag.can_restore())

        with self.assertRaises(exc.ForbiddenError):
            ag.restore()

        c.restore()
        self.assertTrue(ag.get_current_settings().archived)
        self.assertTrue(ag.can_restore())

        ag.restore()
        self.assertFalse(ag.get_current_settings().archived)


class AdGroupTestCase(TestCase):
    fixtures = ['test_api.yaml']

    def test_queryset_exclude_archived(self):
        qs = models.AdGroup.objects.all().exclude_archived()

        self.assertEqual(len(qs), 6)


class CampaignTestCase(TestCase):
    fixtures = ['test_api.yaml']

    def test_queryset_exclude_archived(self):
        qs = models.Campaign.objects.all().exclude_archived()

        self.assertEqual(len(qs), 4)


class AccountTestCase(TestCase):
    fixtures = ['test_api.yaml']

    def test_queryset_exclude_archived(self):
        qs = models.Account.objects.all().exclude_archived()

        self.assertEqual(len(qs), 2)
