from django.test import TestCase

import mock

from utils.magic_mixer import magic_mixer
import core.models
import dash.constants

from . import models, constants, service


class TestGetAnyAppliedFilters(TestCase):
    def setUp(self):
        self.source1 = magic_mixer.blend(
            core.models.Source, id=1, content_ad_submission_policy=dash.constants.SourceSubmissionPolicy.AUTOMATIC
        )
        self.source2 = magic_mixer.blend(
            core.models.Source, id=2, content_ad_submission_policy=dash.constants.SourceSubmissionPolicy.MANUAL
        )

    def test_lookup(self):
        agency1 = magic_mixer.blend(core.models.Agency, id=1)
        agency2 = magic_mixer.blend(core.models.Agency, id=2)
        sf1 = models.SubmissionFilter.objects.create(
            self.source1, constants.SubmissionFilterState.BLOCK, agency=agency1
        )
        sf2 = models.SubmissionFilter.objects.create(
            self.source2, constants.SubmissionFilterState.ALLOW, agency=agency1
        )
        sf3 = models.SubmissionFilter.objects.create(
            self.source2, constants.SubmissionFilterState.ALLOW, agency=agency2
        )
        self.assertEqual(
            service._get_any_applied_filters(dict(agency=agency1)), {(1, "agency", 1): sf1, (2, "agency", 1): sf2}
        )
        self.assertEqual(service._get_any_applied_filters(dict(agency=agency2)), {(2, "agency", 2): sf3})
        self.assertEqual(
            service._get_any_applied_filters(dict(agency__in=[agency1, agency2])),
            {(1, "agency", 1): sf1, (2, "agency", 1): sf2, (2, "agency", 2): sf3},
        )
        # Lookup keys ORed
        self.assertEqual(
            service._get_any_applied_filters(dict(agency=agency2, source__in=[magic_mixer.blend(core.models.Source)])),
            {(2, "agency", 2): sf3},
        )
        self.assertEqual(service._get_any_applied_filters(dict(source=magic_mixer.blend(core.models.Source))), {})

    def test_lookup_multiple_levels(self):
        agency1 = magic_mixer.blend(core.models.Agency, id=1)
        account1 = magic_mixer.blend(core.models.Account, id=1)
        account2 = magic_mixer.blend(core.models.Account, id=2)
        campaign1 = magic_mixer.blend(core.models.Campaign, id=1)
        ad_group1 = magic_mixer.blend(core.models.AdGroup, id=1)
        content_ad1 = magic_mixer.blend(core.models.ContentAd, id=1)
        sf1 = models.SubmissionFilter.objects.create(
            self.source1, constants.SubmissionFilterState.BLOCK, agency=agency1
        )
        sf2 = models.SubmissionFilter.objects.create(
            self.source2, constants.SubmissionFilterState.ALLOW, account=account1
        )
        sf3 = models.SubmissionFilter.objects.create(
            self.source2, constants.SubmissionFilterState.ALLOW, account=account2
        )
        sf4 = models.SubmissionFilter.objects.create(
            self.source1, constants.SubmissionFilterState.BLOCK, campaign=campaign1
        )
        sf5 = models.SubmissionFilter.objects.create(
            self.source1, constants.SubmissionFilterState.BLOCK, content_ad=content_ad1
        )
        sf6 = models.SubmissionFilter.objects.create(
            self.source2, constants.SubmissionFilterState.ALLOW, ad_group=ad_group1
        )
        self.assertEqual(
            service._get_any_applied_filters(dict(agency__in=[agency1], account__in=[account1])),
            {(1, "agency", 1): sf1, (2, "account", 1): sf2},
        )
        self.assertEqual(
            service._get_any_applied_filters(
                dict(campaign__in=[campaign1], account__in=[account1, account2], ad_group_id__in=[ad_group1.pk])
            ),
            {(2, "account", 1): sf2, (2, "account", 2): sf3, (1, "campaign", 1): sf4, (2, "ad_group", 1): sf6},
        )
        self.assertEqual(
            service._get_any_applied_filters(
                dict(campaign__in=[campaign1], agency__in=[agency1], content_ad__in=[content_ad1])
            ),
            {(1, "agency", 1): sf1, (1, "campaign", 1): sf4, (1, "content_ad", 1): sf5},
        )


class TestFilterValidContentAdSources(TestCase):
    def setUp(self):
        pass

    def _create_content_ad_source_dict(
        self, content_ad_id, ad_group_id, campaign_id, account_id, agency_id, source_id, policy
    ):
        return {
            "content_ad_id": content_ad_id,
            "content_ad__ad_group_id": ad_group_id,
            "content_ad__ad_group__campaign_id": campaign_id,
            "content_ad__ad_group__campaign__account_id": account_id,
            "content_ad__ad_group__campaign__account__agency_id": agency_id,
            "source_id": source_id,
            "source__content_ad_submission_policy": policy,
        }

    @mock.patch("dash.features.submission_filters.service._get_any_applied_filters")
    def test_no_filters(self, get_any):
        get_any.return_value = {}
        content_ad_sources = [
            self._create_content_ad_source_dict(1, 1, 1, 1, 1, 1, dash.constants.SourceSubmissionPolicy.AUTOMATIC),
            self._create_content_ad_source_dict(1, 1, 1, 1, 1, 2, dash.constants.SourceSubmissionPolicy.MANUAL),
        ]
        self.assertEqual(
            service.filter_valid_content_ad_sources(content_ad_sources),
            [self._create_content_ad_source_dict(1, 1, 1, 1, 1, 1, dash.constants.SourceSubmissionPolicy.AUTOMATIC)],
        )

    @mock.patch("dash.features.submission_filters.service._get_any_applied_filters")
    def test_allowed_account(self, get_any):
        get_any.return_value = {
            (2, "account", 1000): models.SubmissionFilter(state=constants.SubmissionFilterState.ALLOW)
        }
        content_ad_sources = [
            self._create_content_ad_source_dict(
                1, 10, 100, 1000, 10000, 1, dash.constants.SourceSubmissionPolicy.AUTOMATIC
            ),
            self._create_content_ad_source_dict(
                1, 10, 100, 1000, 10000, 2, dash.constants.SourceSubmissionPolicy.MANUAL
            ),
        ]
        self.assertEqual(
            service.filter_valid_content_ad_sources(content_ad_sources),
            [
                self._create_content_ad_source_dict(
                    1, 10, 100, 1000, 10000, 1, dash.constants.SourceSubmissionPolicy.AUTOMATIC
                ),
                self._create_content_ad_source_dict(
                    1, 10, 100, 1000, 10000, 2, dash.constants.SourceSubmissionPolicy.MANUAL
                ),
            ],
        )

    @mock.patch("dash.features.submission_filters.service._get_any_applied_filters")
    def test_blocked_account(self, get_any):
        get_any.return_value = {
            (1, "account", 1000): models.SubmissionFilter(state=constants.SubmissionFilterState.BLOCK)
        }
        content_ad_sources = [
            self._create_content_ad_source_dict(
                1, 10, 100, 1000, 10000, 1, dash.constants.SourceSubmissionPolicy.AUTOMATIC
            ),
            self._create_content_ad_source_dict(
                1, 10, 100, 1000, 10000, 2, dash.constants.SourceSubmissionPolicy.MANUAL
            ),
        ]
        self.assertEqual(service.filter_valid_content_ad_sources(content_ad_sources), [])

    @mock.patch("dash.features.submission_filters.service._get_any_applied_filters")
    def test_allowed_content_ad(self, get_any):
        get_any.return_value = {
            (2, "content_ad", 1): models.SubmissionFilter(state=constants.SubmissionFilterState.ALLOW)
        }
        content_ad_sources = [
            self._create_content_ad_source_dict(1, 1, 1, 1, 1, 1, dash.constants.SourceSubmissionPolicy.AUTOMATIC),
            self._create_content_ad_source_dict(1, 1, 1, 1, 1, 2, dash.constants.SourceSubmissionPolicy.MANUAL),
        ]
        self.assertEqual(
            service.filter_valid_content_ad_sources(content_ad_sources),
            [
                self._create_content_ad_source_dict(1, 1, 1, 1, 1, 1, dash.constants.SourceSubmissionPolicy.AUTOMATIC),
                self._create_content_ad_source_dict(1, 1, 1, 1, 1, 2, dash.constants.SourceSubmissionPolicy.MANUAL),
            ],
        )

    @mock.patch("dash.features.submission_filters.service._get_any_applied_filters")
    def test_blocked_content_ad(self, get_any):
        get_any.return_value = {
            (1, "content_ad", 1): models.SubmissionFilter(state=constants.SubmissionFilterState.BLOCK),
            (2, "content_ad", 1): models.SubmissionFilter(state=constants.SubmissionFilterState.ALLOW),
        }
        content_ad_sources = [
            self._create_content_ad_source_dict(1, 1, 1, 1, 1, 1, dash.constants.SourceSubmissionPolicy.AUTOMATIC),
            self._create_content_ad_source_dict(1, 1, 1, 1, 1, 2, dash.constants.SourceSubmissionPolicy.MANUAL),
        ]
        self.assertEqual(
            service.filter_valid_content_ad_sources(content_ad_sources),
            [self._create_content_ad_source_dict(1, 1, 1, 1, 1, 2, dash.constants.SourceSubmissionPolicy.MANUAL)],
        )
