from django.test import TestCase

import core.models
import dash.constants
from utils.magic_mixer import magic_mixer

from . import service


class AdReviewServiceTest(TestCase):
    def test_get_per_source_submission_status_map_queryset(self):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        source = magic_mixer.blend(core.models.Source)
        source2 = magic_mixer.blend(core.models.Source)
        content_ad = magic_mixer.blend(core.models.ContentAd, ad_group=ad_group)
        magic_mixer.blend(core.models.ContentAdSource, content_ad=content_ad, source=source)
        magic_mixer.blend(core.models.ContentAdSource, content_ad=content_ad, source=source2)

        per_source_status_map = service.get_per_source_submission_status_map(
            core.models.ContentAd.objects.filter(ad_group=ad_group)
        )

        self.assertEqual(
            per_source_status_map,
            {
                content_ad.id: {
                    source.id: {
                        "source_id": source.id,
                        "submission_status": dash.constants.ContentAdSubmissionStatus.PENDING,
                        "bidder_slug": source.bidder_slug,
                        "submission_errors": None,
                    },
                    source2.id: {
                        "source_id": source2.id,
                        "submission_status": dash.constants.ContentAdSubmissionStatus.PENDING,
                        "bidder_slug": source2.bidder_slug,
                        "submission_errors": None,
                    },
                }
            },
        )

    def test_add_submission_status_list(self):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        source = magic_mixer.blend(core.models.Source)
        content_ads = magic_mixer.cycle(2).blend(core.models.ContentAd, ad_group=ad_group)
        for content_ad in content_ads:
            magic_mixer.blend(core.models.ContentAdSource, content_ad=content_ad, source=source)

        per_source_status_map = service.get_per_source_submission_status_map(content_ads)

        self.assertEqual(
            per_source_status_map,
            {
                content_ads[0].id: {
                    source.id: {
                        "source_id": source.id,
                        "submission_status": dash.constants.ContentAdSubmissionStatus.PENDING,
                        "bidder_slug": source.bidder_slug,
                        "submission_errors": None,
                    }
                },
                content_ads[1].id: {
                    source.id: {
                        "source_id": source.id,
                        "submission_status": dash.constants.ContentAdSubmissionStatus.PENDING,
                        "bidder_slug": source.bidder_slug,
                        "submission_errors": None,
                    }
                },
            },
        )
