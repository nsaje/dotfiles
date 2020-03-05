import mock
from django.test import TestCase

import core.features.goals
import core.models
from utils import dates_helper
from utils.magic_mixer import magic_mixer

from . import content_ads


class PrepareContentAdSettingsTestCase(TestCase):
    @mock.patch("automation.autopilot.recalculate_budgets_ad_group", mock.MagicMock())
    def test_prepare_content_ad_settings(self):
        self.utc_today = dates_helper.utc_today()
        ad_group = magic_mixer.blend(core.models.AdGroup)
        content_ad = magic_mixer.blend(core.models.ContentAd, ad_group=ad_group, label="test")
        self.assertEqual(
            content_ads.prepare_content_ad_settings([ad_group]),
            {
                ad_group.id: {
                    content_ad.id: {
                        "ad_created_date": self.utc_today,
                        "ad_group_id": ad_group.id,
                        "ad_label": content_ad.label,
                        "ad_title": content_ad.title,
                        "content_ad_id": content_ad.id,
                        "days_since_ad_created": 0,
                    }
                }
            },
        )
