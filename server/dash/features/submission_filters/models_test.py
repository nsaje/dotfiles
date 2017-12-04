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
        self.assertEquals(
            models.SubmissionFilter.objects.all().filter_applied(self.source1, ad_group=self.ad_group1).count(),
            1
        )

    def test_filter_applied_campaign(self):
        magic_mixer.blend(models.SubmissionFilter,
                          source=self.source1, campaign=self.ad_group1.campaign,
                          state=constants.SubmissionFilterState.BLOCK)
        self.assertEquals(
            models.SubmissionFilter.objects.all().filter_applied(
                self.source1, ad_group=self.ad_group1
            ).count(),
            1
        )
        self.assertEquals(
            models.SubmissionFilter.objects.all().filter_applied(
                self.source2, ad_group=self.ad_group1
            ).count(),
            0
        )
        self.assertEquals(
            models.SubmissionFilter.objects.all().filter_applied(
                self.source1, account=self.ad_group1.campaign.account
            ).count(),
            0
        )

    def test_filter_applied_account(self):
        magic_mixer.blend(models.SubmissionFilter,
                          source=self.source1, account=self.ad_group1.campaign.account,
                          state=constants.SubmissionFilterState.BLOCK)
        self.assertEquals(
            models.SubmissionFilter.objects.all().filter_applied(
                self.source1, ad_group=self.ad_group1
            ).count(),
            1
        )
        self.assertEquals(
            models.SubmissionFilter.objects.all().filter_applied(
                self.source1, campaign=self.ad_group1.campaign
            ).count(),
            1
        )
        self.assertEquals(
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
        self.assertEquals(
            models.SubmissionFilter.objects.all().filter_applied(
                self.source1, ad_group=self.ad_group1
            ).count(),
            1
        )
        self.assertEquals(
            models.SubmissionFilter.objects.all().filter_applied(
                self.source1, campaign=self.ad_group1.campaign
            ).count(),
            1
        )
        self.assertEquals(
            models.SubmissionFilter.objects.all().filter_applied(
                self.source1, account=self.ad_group1.campaign.account
            ).count(),
            1
        )
        self.assertEquals(
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
        self.assertEquals(
            models.SubmissionFilter.objects.all().filter_applied(
                self.source1, content_ad=ad
            ).count(),
            1
        )
        self.assertEquals(
            models.SubmissionFilter.objects.all().filter_applied(
                self.source1, ad_group=self.ad_group1
            ).count(),
            0
        )

        self.assertEquals(
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

    def test_ad_group(self):
        ad_group = magic_mixer.blend(core.entity.AdGroup)
        self.assertTrue(models.SubmissionFilter.objects.create(
            self.source1,
            constants.SubmissionFilterState.BLOCK,
            ad_group=ad_group,
        ))

    def test_campaign(self):
        campaign = magic_mixer.blend(core.entity.Campaign)
        self.assertTrue(models.SubmissionFilter.objects.create(
            self.source1,
            constants.SubmissionFilterState.BLOCK,
            campaign=campaign,
        ))

    def test_account(self):
        account = magic_mixer.blend(core.entity.Account)
        self.assertTrue(models.SubmissionFilter.objects.create(
            self.source2,
            constants.SubmissionFilterState.ALLOW,
            account=account,
        ))

    def test_agency(self):
        agency = magic_mixer.blend(core.entity.Agency)
        self.assertTrue(models.SubmissionFilter.objects.create(
            self.source2,
            constants.SubmissionFilterState.ALLOW,
            agency=agency,
        ))

    def test_content_ad(self):
        ad = magic_mixer.blend(core.entity.ContentAd)
        self.assertTrue(models.SubmissionFilter.objects.create(
            self.source2,
            constants.SubmissionFilterState.ALLOW,
            content_ad=ad,
        ))

    def test_ad_group_duplicate(self):
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

    def test_ad_group_invalid_allow(self):
        ad_group = magic_mixer.blend(core.entity.AdGroup)
        with self.assertRaises(exceptions.SourcePolicyException):
            models.SubmissionFilter.objects.create(
                self.source1,
                constants.SubmissionFilterState.ALLOW,
                ad_group=ad_group,
            )

    def test_ad_group_invalid_block(self):
        ad_group = magic_mixer.blend(core.entity.AdGroup)
        with self.assertRaises(exceptions.SourcePolicyException):
            models.SubmissionFilter.objects.create(
                self.source2,
                constants.SubmissionFilterState.BLOCK,
                ad_group=ad_group,
            )

    def test_multiple_entities(self):
        ad_group = magic_mixer.blend(core.entity.AdGroup)
        campaign = magic_mixer.blend(core.entity.Campaign)
        with self.assertRaises(exceptions.MultipleFilterEntitiesException):
            models.SubmissionFilter.objects.create(
                self.source1,
                constants.SubmissionFilterState.BLOCK,
                ad_group=ad_group,
                campaign=campaign,
            )
