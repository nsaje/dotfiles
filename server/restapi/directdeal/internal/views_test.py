from django.urls import reverse

import core.features.deals
import core.models
from restapi.common.views_base_test import RESTAPITest
from utils.magic_mixer import magic_mixer


class DirectDealViewSetTest(RESTAPITest):
    def test_validate_empty(self):
        r = self.client.post(reverse("restapi.directdeal.internal:directdeal_validate"))
        self.assertResponseValid(r, data_type=type(None))

    def test_validate(self):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        source = magic_mixer.blend(core.models.Source)
        data = {"dealId": "DEAL_123", "source": source.bidder_slug, "agencyId": agency.id}
        r = self.client.post(reverse("restapi.directdeal.internal:directdeal_validate"), data=data, format="json")
        self.assertResponseValid(r, data_type=type(None))

    def test_validate_error(self):
        data = {"dealId": None, "source": None, "agencyId": None}
        r = self.client.post(reverse("restapi.directdeal.internal:directdeal_validate"), data=data, format="json")
        r = self.assertResponseError(r, "ValidationError")
        self.assertIn("This field may not be null.", r["details"]["dealId"][0])
        self.assertIn("This field may not be null.", r["details"]["source"][0])

    def test_validate_source_error(self):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        data = {"dealId": "DEAL_123", "source": "12345", "agencyId": agency.id}
        r = self.client.post(reverse("restapi.directdeal.internal:directdeal_validate"), data=data, format="json")
        r = self.assertResponseError(r, "DoesNotExist")
        self.assertIn("Source matching query does not exist.", r["details"])

    def test_get(self):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        source = magic_mixer.blend(core.models.Source)
        deal = magic_mixer.blend(
            core.features.deals.DirectDeal, agency=agency, source=source, deal_id="DEAL_123", name="DEAL 123"
        )

        r = self.client.get(reverse("restapi.directdeal.internal:directdeal_details", kwargs={"deal_id": deal.id}))
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
            reverse("restapi.directdeal.internal:directdeal_list"), {"agencyId": agency.id, "offset": 0, "limit": 20}
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(resp_json["count"], 20)
        self.assertIsNone(resp_json["next"])

        r_paginated = self.client.get(
            reverse("restapi.directdeal.internal:directdeal_list"), {"agencyId": agency.id, "offset": 10, "limit": 10}
        )
        resp_json_paginated = self.assertResponseValid(r_paginated, data_type=list)

        self.assertEqual(resp_json_paginated["count"], 20)
        self.assertIsNotNone(resp_json_paginated["previous"])
        self.assertIsNone(resp_json_paginated["next"])

        self.assertEqual(resp_json["data"][10:20], resp_json_paginated["data"])

    def test_list_with_keyword(self):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        source = magic_mixer.blend(core.models.Source, name="Test name", bidder_slug="Test bidder_slug")

        magic_mixer.blend(core.features.deals.DirectDeal, agency=agency, source=source, name="Deal 1", deal_id="DEAL_1")
        magic_mixer.blend(core.features.deals.DirectDeal, agency=agency, source=source, name="Deal 2", deal_id="DEAL_2")
        magic_mixer.blend(core.features.deals.DirectDeal, agency=agency, source=source, name="Deal 3", deal_id="DEAL_3")

        r = self.client.get(
            reverse("restapi.directdeal.internal:directdeal_list"),
            {"offset": 0, "limit": 20, "keyword": "test", "agencyId": agency.id},
        )
        resp_json = self.assertResponseValid(r, data_type=list)

        self.assertEqual(resp_json["count"], 3)
        self.assertIsNone(resp_json["previous"])
        self.assertIsNone(resp_json["next"])

        r = self.client.get(
            reverse("restapi.directdeal.internal:directdeal_list"),
            {"offset": 0, "limit": 20, "keyword": "DEAL_1", "agencyId": agency.id},
        )
        resp_json = self.assertResponseValid(r, data_type=list)

        self.assertEqual(resp_json["count"], 1)
        self.assertIsNone(resp_json["previous"])
        self.assertIsNone(resp_json["next"])

        self.assertEqual(resp_json["data"][0]["dealId"], "DEAL_1")

    def test_put(self):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        source = magic_mixer.blend(core.models.Source)
        deal = magic_mixer.blend(
            core.features.deals.DirectDeal, agency=agency, source=source, deal_id="DEAL_123", name="DEAL 123"
        )

        r = self.client.get(reverse("restapi.directdeal.internal:directdeal_details", kwargs={"deal_id": deal.id}))
        resp_json = self.assertResponseValid(r)

        name = "DEAL 123 (UPDATED)"
        description = "DEAL 123 EXTRA TEXT"

        put_data = resp_json["data"].copy()
        put_data["name"] = name
        put_data["description"] = description
        put_data["agencyId"] = agency.id

        r = self.client.put(
            reverse("restapi.directdeal.internal:directdeal_details", kwargs={"deal_id": deal.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)

        self.assertEqual(resp_json["data"]["name"], name)
        self.assertEqual(resp_json["data"]["description"], description)

    def test_post(self):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        source = magic_mixer.blend(core.models.Source)

        new_deal = {"dealId": "DEAL_444", "source": source.bidder_slug, "name": "DEAL 444", "agencyId": agency.id}

        r = self.client.post(reverse("restapi.directdeal.internal:directdeal_list"), data=new_deal, format="json")
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

        r = self.client.get(reverse("restapi.directdeal.internal:directdeal_details", kwargs={"deal_id": deal.id}))
        resp_json = self.assertResponseValid(r)

        self.assertIsNotNone(resp_json["data"]["id"])
        self.assertEqual(resp_json["data"]["id"], str(deal.id))

        r = self.client.delete(reverse("restapi.directdeal.internal:directdeal_details", kwargs={"deal_id": deal.id}))
        self.assertEqual(r.status_code, 204)

        r = self.client.get(reverse("restapi.directdeal.internal:directdeal_details", kwargs={"deal_id": deal.id}))
        self.assertResponseError(r, "MissingDataError")

    def test_list_connections(self):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])

        account = magic_mixer.blend(core.models.Account, agency=agency, name="Demo account")
        account.settings.update_unsafe(None, name=account.name)

        campaign = magic_mixer.blend(core.models.Campaign, account=account, name="Demo campaign")
        campaign.settings.update_unsafe(None, name=campaign.name)

        adgroup = magic_mixer.blend(core.models.AdGroup, campaign=campaign, name="Demo adgroup")
        adgroup.settings.update_unsafe(None, ad_group_name=adgroup.name)

        source = magic_mixer.blend(core.models.Source)

        deal = magic_mixer.blend(core.features.deals.DirectDeal, agency=agency, source=source)
        deal_connection_account = magic_mixer.blend(
            core.features.deals.DirectDealConnection, deal=deal, account=account
        )
        deal_connection_campaign = magic_mixer.blend(
            core.features.deals.DirectDealConnection, deal=deal, campaign=campaign
        )
        deal_connection_adgroup = magic_mixer.blend(
            core.features.deals.DirectDealConnection, deal=deal, adgroup=adgroup
        )

        r = self.client.get(
            reverse("restapi.directdeal.internal:directdealconnection_list", kwargs={"deal_id": deal.id})
        )
        resp_json = self.assertResponseValid(r, data_type=list)

        self.assertEqual(
            resp_json["data"],
            [
                {
                    "id": str(deal_connection_adgroup.id),
                    "account": {},
                    "campaign": {},
                    "adgroup": {
                        "id": str(deal_connection_adgroup.adgroup.id),
                        "name": deal_connection_adgroup.adgroup.settings.ad_group_name,
                    },
                },
                {
                    "id": str(deal_connection_campaign.id),
                    "account": {},
                    "campaign": {
                        "id": str(deal_connection_campaign.campaign.id),
                        "name": deal_connection_campaign.campaign.settings.name,
                    },
                    "adgroup": {},
                },
                {
                    "id": str(deal_connection_account.id),
                    "account": {
                        "id": str(deal_connection_account.account.id),
                        "name": deal_connection_account.account.settings.name,
                    },
                    "campaign": {},
                    "adgroup": {},
                },
            ],
        )

    def test_remove_connection(self):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])

        account = magic_mixer.blend(core.models.Account, agency=agency, name="Demo account")
        account.settings.update_unsafe(None, name=account.name)

        source = magic_mixer.blend(core.models.Source)

        deal = magic_mixer.blend(core.features.deals.DirectDeal, agency=agency, source=source)
        deal_connection_account = magic_mixer.blend(
            core.features.deals.DirectDealConnection, deal=deal, account=account
        )

        r = self.client.get(
            reverse("restapi.directdeal.internal:directdealconnection_list", kwargs={"deal_id": deal.id})
        )
        resp_json = self.assertResponseValid(r, data_type=list)

        self.assertEqual(
            resp_json["data"],
            [
                {
                    "id": str(deal_connection_account.id),
                    "account": {
                        "id": str(deal_connection_account.account.id),
                        "name": deal_connection_account.account.settings.name,
                    },
                    "campaign": {},
                    "adgroup": {},
                }
            ],
        )

        r = self.client.delete(
            reverse(
                "restapi.directdeal.internal:directdealconnection_details",
                kwargs={"deal_id": deal.id, "deal_connection_id": deal_connection_account.id},
            )
        )
        self.assertEqual(r.status_code, 204)

        r = self.client.get(
            reverse("restapi.directdeal.internal:directdealconnection_list", kwargs={"deal_id": deal.id})
        )
        resp_json = self.assertResponseValid(r, data_type=list)

        self.assertEqual(resp_json["data"], [])
