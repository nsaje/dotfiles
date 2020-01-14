import json

from django.urls import reverse

import core.models
from utils import zlogging
from utils.magic_mixer import magic_mixer

from .base_test import K1APIBaseTest

logger = zlogging.getLogger(__name__)
logger.setLevel(zlogging.INFO)


class R1PixelMappingTest(K1APIBaseTest):
    def test_get_account_slugs(self):
        response = self.client.get(reverse("k1api.r1_pixel_mapping", kwargs={"account_id": 1}))
        resp_json = json.loads(response.content)
        self.assert_response_ok(response, resp_json)
        self.assertEqual(2, len(resp_json["response"]))


class R1AdGroupMappingTest(K1APIBaseTest):
    def test_get_account_ad_groups_campaigns(self):
        response = self.client.get(reverse("k1api.r1_ad_group_mapping", kwargs={"account_id": 1}))
        resp_json = json.loads(response.content)
        self.assert_response_ok(response, resp_json)
        self.assertEqual(
            [{"ad_group_id": 1, "campaign_id": 1}, {"ad_group_id": 2, "campaign_id": 1}], resp_json["response"]
        )

    def test_get_account_ad_groups_campaigns_paginated(self):
        account = magic_mixer.blend(core.models.Account)
        magic_mixer.cycle(5).blend(core.models.Campaign, account=account)

        expected_result = []
        for c in account.campaign_set.all():
            for ag in magic_mixer.cycle(3).blend(core.models.AdGroup, campaign=c):
                expected_result.append({"ad_group_id": ag.id, "campaign_id": c.id})

        response = self.client.get(
            reverse("k1api.r1_ad_group_mapping", kwargs={"account_id": account.id}), {"limit": 2}
        )
        resp_json = json.loads(response.content)
        self.assert_response_ok(response, resp_json)
        data = resp_json["response"]
        self.assertEqual(2, len(data))
        result = self._validate_and_update_pagination_result([], data)

        page_count = 1
        while len(data) == 2:
            response = self.client.get(
                reverse("k1api.r1_ad_group_mapping", kwargs={"account_id": account.id}),
                {"limit": 2, "marker": data[-1]["ad_group_id"]},
            )
            resp_json = json.loads(response.content)
            self.assert_response_ok(response, resp_json)
            data = resp_json["response"]
            result = self._validate_and_update_pagination_result(result, data)
            page_count += 1

        self.assertEqual(8, page_count)
        self.assertEqual(expected_result, result)

    def _validate_and_update_pagination_result(self, result, data):
        for mapping in data:
            self.assertNotIn(mapping, result)
        result.extend(data)
        return result
