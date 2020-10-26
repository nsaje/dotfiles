import decimal

import mock
from django.urls import reverse

import core.models
import core.models.ad_group
from restapi.common.views_base_test_case import RESTAPITestCase
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission


class RealtimestatsViewsTest(RESTAPITestCase):
    @mock.patch("dash.features.realtimestats.get_ad_group_sources_stats")
    def test_adgroup_sources_realtimestats(self, mock_get):
        account = self.mix_account(self.user, permissions=[Permission.READ])
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account=account)

        sources = magic_mixer.cycle(2).blend(core.models.Source, bidder_slug=magic_mixer.RANDOM)
        data = {
            "spend": [
                {"source": sources[0], "spend": decimal.Decimal("12.34567")},
                {"source": sources[1], "spend": decimal.Decimal("0.11111")},
            ],
            "clicks": 65464,
            "impressions": 465973,
        }

        mock_get.return_value = data
        r = self.client.get(
            reverse(
                "restapi.adgroupsourcestats.internal:adgroups_realtimestats_sources",
                kwargs={"ad_group_id": ad_group.id},
            )
        )

        resp_json = self.assertResponseValid(r)

        expected = {
            "spend": [{"source": sources[0].name, "spend": "12.35"}, {"source": sources[1].name, "spend": "0.11"}],
            "clicks": 65464,
            "impressions": 465973,
        }
        self.assertEqual(resp_json["data"], expected)

        mock_get.assert_called_with(ad_group, use_local_currency=True)
