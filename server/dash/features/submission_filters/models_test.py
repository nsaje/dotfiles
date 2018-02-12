from django.test import TestCase

from utils.magic_mixer import magic_mixer

import zemauth.models
import core.entity
import dash.constants

from . import models, constants, exceptions


class TestModels(TestCase):
    def setUp(self):
        self.source1 = magic_mixer.blend(core.source.Source)
        self.source2 = magic_mixer.blend(core.source.Source)

        self.ad_group1 = magic_mixer.blend(core.entity.AdGroup)
        magic_mixer.blend(models.SubmissionFilter, source=self.source2, ad_group=magic_mixer.blend(core.entity.AdGroup),
                          state=constants.SubmissionFilterState.ALLOW)

    def test_filter_applied_ad_group(self):
        magic_mixer.blend(models.SubmissionFilter, source=self.source1, ad_group=self.ad_group1,
                          state=constants.SubmissionFilterState.BLOCK)
        self.assertEqual(
            models.SubmissionFilter.objects.all().filter_applied(self.source1, ad_group=self.ad_group1).count(),
            1
        )

    def test_filter_applied_campaign(self):
        magic_mixer.blend(models.SubmissionFilter,
                          source=self.source1, campaign=self.ad_group1.campaign,
                          state=constants.SubmissionFilterState.BLOCK)
        self.assertEqual(
            models.SubmissionFilter.objects.all().filter_applied(
                self.source1, ad_group=self.ad_group1
            ).count(),
            1
        )
        self.assertEqual(
            models.SubmissionFilter.objects.all().filter_applied(
                self.source2, ad_group=self.ad_group1
            ).count(),
            0
        )
        self.assertEqual(
            models.SubmissionFilter.objects.all().filter_applied(
                self.source1, account=self.ad_group1.campaign.account
            ).count(),
            0
        )

    def test_filter_applied_account(self):
        magic_mixer.blend(models.SubmissionFilter,
                          source=self.source1, account=self.ad_group1.campaign.account,
                          state=constants.SubmissionFilterState.BLOCK)
        self.assertEqual(
            models.SubmissionFilter.objects.all().filter_applied(
                self.source1, ad_group=self.ad_group1
            ).count(),
            1
        )
        self.assertEqual(
            models.SubmissionFilter.objects.all().filter_applied(
                self.source1, campaign=self.ad_group1.campaign
            ).count(),
            1
        )
        self.assertEqual(
            models.SubmissionFilter.objects.all().filter_applied(
                self.source1, account=self.ad_group1.campaign.account
            ).count(),
            1
        )

    def test_filter_applied_agency(self):
        class Req:
            user = magic_mixer.blend(zemauth.models.User)
        self.ad_group1.campaign.account.agency = magic_mixer.blend(core.entity.Agency)
        self.ad_group1.campaign.account.save(Req())
        magic_mixer.blend(models.SubmissionFilter,
                          source=self.source1, agency=self.ad_group1.campaign.account.agency,
                          state=constants.SubmissionFilterState.BLOCK)
        self.assertEqual(
            models.SubmissionFilter.objects.all().filter_applied(
                self.source1, ad_group=self.ad_group1
            ).count(),
            1
        )
        self.assertEqual(
            models.SubmissionFilter.objects.all().filter_applied(
                self.source1, campaign=self.ad_group1.campaign
            ).count(),
            1
        )
        self.assertEqual(
            models.SubmissionFilter.objects.all().filter_applied(
                self.source1, account=self.ad_group1.campaign.account
            ).count(),
            1
        )
        self.assertEqual(
            models.SubmissionFilter.objects.all().filter_applied(
                self.source1, agency=self.ad_group1.campaign.account.agency
            ).count(),
            1
        )

    def test_filter_applied_content_ad(self):
        ad = magic_mixer.blend(core.entity.ContentAd, ad_group=self.ad_group1)

        magic_mixer.blend(models.SubmissionFilter,
                          source=self.source1, content_ad=ad,
                          state=constants.SubmissionFilterState.ALLOW)
        self.assertEqual(
            models.SubmissionFilter.objects.all().filter_applied(
                self.source1, content_ad=ad
            ).count(),
            1
        )
        self.assertEqual(
            models.SubmissionFilter.objects.all().filter_applied(
                self.source1, ad_group=self.ad_group1
            ).count(),
            0
        )

        self.assertEqual(
            models.SubmissionFilter.objects.all().filter_applied(
                self.source2, content_ad=ad
            ).count(),
            0
        )


class TestManager(TestCase):
    def setUp(self):
        self.source1 = magic_mixer.blend(
            core.source.Source, content_ad_submission_policy=dash.constants.SourceSubmissionPolicy.AUTOMATIC)
        self.source2 = magic_mixer.blend(
            core.source.Source, content_ad_submission_policy=dash.constants.SourceSubmissionPolicy.MANUAL)

    def test_ad_group_bulk_create(self):
        ad_group1 = magic_mixer.blend(core.entity.AdGroup)
        ad_group2 = magic_mixer.blend(core.entity.AdGroup)
        sf_list = models.SubmissionFilter.objects.bulk_create(
            self.source1,
            constants.SubmissionFilterState.BLOCK,
            'ad_group',
            [ad_group1.pk, ad_group2.pk]
        )
        self.assertEqual(
            set([constants.SubmissionFilterState.BLOCK]),
            set(sf.state for sf in sf_list)
        )
        self.assertEqual(
            set([ad_group1.pk, ad_group2.pk]),
            set(sf.ad_group_id for sf in sf_list)
        )

    def test_campaign_bulk_create(self):
        campaign1 = magic_mixer.blend(core.entity.Campaign)
        campaign2 = magic_mixer.blend(core.entity.Campaign)
        sf_list = models.SubmissionFilter.objects.bulk_create(
            self.source1,
            constants.SubmissionFilterState.BLOCK,
            'campaign',
            [campaign1.pk, campaign2.pk]
        )
        self.assertEqual(
            set([campaign1.pk, campaign2.pk]),
            set(sf.campaign_id for sf in sf_list)
        )
        self.assertEqual(
            set([constants.SubmissionFilterState.BLOCK]),
            set(sf.state for sf in sf_list)
        )

    def test_ad_group_invalid_allow_bulk_create(self):
        ad_group = magic_mixer.blend(core.entity.AdGroup)
        with self.assertRaises(exceptions.SourcePolicyException):
            models.SubmissionFilter.objects.bulk_create(
                self.source1,
                constants.SubmissionFilterState.ALLOW,
                'ad_group',
                [ad_group.pk]
            )

    def test_ad_group_invalid_block_bulk_create(self):
        ad_group = magic_mixer.blend(core.entity.AdGroup)
        with self.assertRaises(exceptions.SourcePolicyException):
            models.SubmissionFilter.objects.bulk_create(
                self.source2,
                constants.SubmissionFilterState.BLOCK,
                'ad_group',
                [ad_group.pk]
            )

    def test_duplicate_bulk_create(self):
        ad_group = magic_mixer.blend(core.entity.AdGroup)
        models.SubmissionFilter.objects.create(
            self.source1,
            constants.SubmissionFilterState.BLOCK,
            ad_group=ad_group,
        )
        with self.assertRaises(exceptions.SubmissionFilterExistsException):
            models.SubmissionFilter.objects.bulk_create(
                self.source1,
                constants.SubmissionFilterState.BLOCK,
                'ad_group',
                [ad_group.pk]
            )

    def test_ad_group_create(self):
        ad_group = magic_mixer.blend(core.entity.AdGroup)
        self.assertTrue(models.SubmissionFilter.objects.create(
            self.source1,
            constants.SubmissionFilterState.BLOCK,
            ad_group=ad_group,
        ))

    def test_campaign_create(self):
        campaign = magic_mixer.blend(core.entity.Campaign)
        self.assertTrue(models.SubmissionFilter.objects.create(
            self.source1,
            constants.SubmissionFilterState.BLOCK,
            campaign=campaign,
        ))

    def test_account_create(self):
        account = magic_mixer.blend(core.entity.Account)
        self.assertTrue(models.SubmissionFilter.objects.create(
            self.source2,
            constants.SubmissionFilterState.ALLOW,
            account=account,
        ))

    def test_agency_create(self):
        agency = magic_mixer.blend(core.entity.Agency)
        self.assertTrue(models.SubmissionFilter.objects.create(
            self.source2,
            constants.SubmissionFilterState.ALLOW,
            agency=agency,
        ))

    def test_content_ad_create(self):
        ad = magic_mixer.blend(core.entity.ContentAd)
        self.assertTrue(models.SubmissionFilter.objects.create(
            self.source2,
            constants.SubmissionFilterState.ALLOW,
            content_ad=ad,
        ))

    def test_ad_group_duplicate_create(self):
        ad_group = magic_mixer.blend(core.entity.AdGroup)
        models.SubmissionFilter.objects.create(
            self.source1,
            constants.SubmissionFilterState.BLOCK,
            ad_group=ad_group,
        )
        with self.assertRaises(exceptions.SubmissionFilterExistsException):
            models.SubmissionFilter.objects.create(
                self.source1,
                constants.SubmissionFilterState.BLOCK,
                ad_group=ad_group,
            )

    def test_ad_group_invalid_allow_create(self):
        ad_group = magic_mixer.blend(core.entity.AdGroup)
        with self.assertRaises(exceptions.SourcePolicyException):
            models.SubmissionFilter.objects.create(
                self.source1,
                constants.SubmissionFilterState.ALLOW,
                ad_group=ad_group,
            )

    def test_ad_group_invalid_block_create(self):
        ad_group = magic_mixer.blend(core.entity.AdGroup)
        with self.assertRaises(exceptions.SourcePolicyException):
            models.SubmissionFilter.objects.create(
                self.source2,
                constants.SubmissionFilterState.BLOCK,
                ad_group=ad_group,
            )

    def test_multiple_entities_create(self):
        ad_group = magic_mixer.blend(core.entity.AdGroup)
        campaign = magic_mixer.blend(core.entity.Campaign)
        with self.assertRaises(exceptions.MultipleFilterEntitiesException):
            models.SubmissionFilter.objects.create(
                self.source1,
                constants.SubmissionFilterState.BLOCK,
                ad_group=ad_group,
                campaign=campaign,
            )
