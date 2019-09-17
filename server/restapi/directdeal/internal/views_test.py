from django.urls import reverse

import core.features.deals
import core.models
from restapi.common.views_base_test import RESTAPITest
from utils.magic_mixer import magic_mixer


class DirectDealViewSetTest(RESTAPITest):
    def test_validate_empty(self):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        r = self.client.post(
            reverse("restapi.directdeal.internal:directdeal_validate", kwargs={"agency_id": agency.id})
        )
        self.assertResponseValid(r, data_type=type(None))

    def test_validate(self):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        source = magic_mixer.blend(core.models.Source)
        data = {"dealId": "DEAL_123", "source": source.bidder_slug}
        r = self.client.post(
            reverse("restapi.directdeal.internal:directdeal_validate", kwargs={"agency_id": agency.id}),
            data=data,
            format="json",
        )
        self.assertResponseValid(r, data_type=type(None))

    def test_validate_error(self):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        data = {"dealId": None, "source": None}
        r = self.client.post(
            reverse("restapi.directdeal.internal:directdeal_validate", kwargs={"agency_id": agency.id}),
            data=data,
            format="json",
        )
        r = self.assertResponseError(r, "ValidationError")
        self.assertIn("This field may not be null.", r["details"]["dealId"][0])
        self.assertIn("This field may not be null.", r["details"]["source"][0])

    def test_validate_source_error(self):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        data = {"dealId": "DEAL_123", "source": "12345"}
        r = self.client.post(
            reverse("restapi.directdeal.internal:directdeal_validate", kwargs={"agency_id": agency.id}),
            data=data,
            format="json",
        )
        r = self.assertResponseError(r, "DoesNotExist")
        self.assertIn("Source matching query does not exist.", r["details"])

    def test_get(self):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        source = magic_mixer.blend(core.models.Source)
        deal = magic_mixer.blend(
            core.features.deals.DirectDeal, agency=agency, source=source, deal_id="DEAL_123", name="DEAL 123"
        )

        r = self.client.get(
            reverse(
                "restapi.directdeal.internal:directdeal_details", kwargs={"agency_id": agency.id, "deal_id": deal.id}
            )
        )
        resp_json = self.assertResponseValid(r)

        self.assertEqual(resp_json["data"]["id"], str(deal.id))
        self.assertEqual(resp_json["data"]["name"], deal.name)
        self.assertEqual(resp_json["data"]["dealId"], deal.deal_id)
        self.assertEqual(resp_json["data"]["source"], source.bidder_slug)

    def test_list_pagination(self):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        source = magic_mixer.blend(core.models.Source)
        magic_mixer.cycle(20).blend(core.features.deals.DirectDeal, agency=agency, source=source)

        r = self.client.get(
            reverse("restapi.directdeal.internal:directdeal_list", kwargs={"agency_id": agency.id}),
            {"offset": 0, "limit": 20},
        )
        resp_json = self.assertResponseValid(r, data_type=list)

        self.assertEqual(resp_json["count"], 20)
        self.assertIsNone(resp_json["previous"])
        self.assertIsNone(resp_json["next"])

        r_paginated = self.client.get(
            reverse("restapi.directdeal.internal:directdeal_list", kwargs={"agency_id": agency.id}),
            {"offset": 10, "limit": 10},
        )
        resp_json_paginated = self.assertResponseValid(r_paginated, data_type=list)

        self.assertEqual(resp_json_paginated["count"], 20)
        self.assertIsNotNone(resp_json_paginated["previous"])
        self.assertIsNone(resp_json_paginated["next"])

        self.assertEqual(resp_json["data"][10:20], resp_json_paginated["data"])

    def test_put(self):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        source = magic_mixer.blend(core.models.Source)
        deal = magic_mixer.blend(
            core.features.deals.DirectDeal, agency=agency, source=source, deal_id="DEAL_123", name="DEAL 123"
        )

        r = self.client.get(
            reverse(
                "restapi.directdeal.internal:directdeal_details", kwargs={"agency_id": agency.id, "deal_id": deal.id}
            )
        )
        resp_json = self.assertResponseValid(r)

        name = "DEAL 123 (UPDATED)"
        description = "DEAL 123 EXTRA TEXT"

        put_data = resp_json["data"].copy()
        put_data["name"] = name
        put_data["description"] = description

        r = self.client.put(
            reverse(
                "restapi.directdeal.internal:directdeal_details", kwargs={"agency_id": agency.id, "deal_id": deal.id}
            ),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)

        self.assertEqual(resp_json["data"]["name"], name)
        self.assertEqual(resp_json["data"]["description"], description)

    def test_post(self):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        source = magic_mixer.blend(core.models.Source)

        new_deal = {"dealId": "DEAL_444", "source": source.bidder_slug, "name": "DEAL 444"}

        r = self.client.post(
            reverse("restapi.directdeal.internal:directdeal_list", kwargs={"agency_id": agency.id}),
            data=new_deal,
            format="json",
        )
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)

        self.assertIsNotNone(resp_json["data"]["id"])
        self.assertEqual(resp_json["data"]["source"], source.bidder_slug)
        self.assertEqual(resp_json["data"]["dealId"], new_deal["dealId"])
        self.assertEqual(resp_json["data"]["name"], new_deal["name"])

    def test_remove(self):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        source = magic_mixer.blend(core.models.Source)
        deal = magic_mixer.blend(
            core.features.deals.DirectDeal, agency=agency, source=source, deal_id="DEAL_123", name="DEAL 123"
        )

        r = self.client.get(
            reverse(
                "restapi.directdeal.internal:directdeal_details", kwargs={"agency_id": agency.id, "deal_id": deal.id}
            )
        )
        resp_json = self.assertResponseValid(r)

        self.assertIsNotNone(resp_json["data"]["id"])
        self.assertEqual(resp_json["data"]["id"], str(deal.id))

        r = self.client.delete(
            reverse(
                "restapi.directdeal.internal:directdeal_details", kwargs={"agency_id": agency.id, "deal_id": deal.id}
            )
        )
        self.assertEqual(r.status_code, 204)

        r = self.client.get(
            reverse(
                "restapi.directdeal.internal:directdeal_details", kwargs={"agency_id": agency.id, "deal_id": deal.id}
            )
        )
        self.assertResponseError(r, "MissingDataError")
