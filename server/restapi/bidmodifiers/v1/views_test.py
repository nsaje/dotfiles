from django.urls import reverse
from rest_framework import status

import core.models
import restapi.common.views_base_test
from core.features import bid_modifiers
from dash import constants
from dash.features import geolocation
from utils import test_helper
from utils.magic_mixer import get_request_mock
from utils.magic_mixer import magic_mixer


class BidModifierViewSetTest(restapi.common.views_base_test.RESTAPITest):
    def setUp(self):
        super(BidModifierViewSetTest, self).setUp()
        test_helper.add_permissions(self.user, ["can_set_bid_modifiers"])
        self.request = get_request_mock(self.user)
        self.source = magic_mixer.blend(core.models.Source, bidder_slug="test_slug")
        self.content_ad = magic_mixer.blend(core.models.ContentAd)
        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account__users=[self.user])
        self.other_ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account__users=[self.user])
        self.foreign_ad_group = magic_mixer.blend(core.models.AdGroup)

        self.us = magic_mixer.blend(
            geolocation.Geolocation, key="US", type=constants.LocationType.COUNTRY, name="United States"
        )
        self.us_tx = magic_mixer.blend(
            geolocation.Geolocation, key="US-TX", type=constants.LocationType.REGION, name="Texas, United States"
        )
        self.ep_tx = magic_mixer.blend(
            geolocation.Geolocation, key="765", type=constants.LocationType.DMA, name="765 El Paso, TX"
        )

        self.bid_modifiers_list = [
            magic_mixer.blend(
                bid_modifiers.BidModifier,
                ad_group=self.ad_group,
                type=bid_modifiers.BidModifierType.PUBLISHER,
                target="example.com",
                source=self.source,
                source_slug=self.source.bidder_slug,
                modifier=0.5,
            ),
            magic_mixer.blend(
                bid_modifiers.BidModifier,
                ad_group=self.ad_group,
                type=bid_modifiers.BidModifierType.SOURCE,
                target=str(self.source.id),
                source=None,
                source_slug="",
                modifier=4.6,
            ),
            magic_mixer.blend(
                bid_modifiers.BidModifier,
                ad_group=self.ad_group,
                type=bid_modifiers.BidModifierType.DEVICE,
                target=str(constants.DeviceType.DESKTOP),
                source=None,
                source_slug="",
                modifier=1.3,
            ),
            magic_mixer.blend(
                bid_modifiers.BidModifier,
                ad_group=self.ad_group,
                type=bid_modifiers.BidModifierType.OPERATING_SYSTEM,
                target=constants.OperatingSystem.LINUX,
                source=None,
                source_slug="",
                modifier=1.7,
            ),
            magic_mixer.blend(
                bid_modifiers.BidModifier,
                ad_group=self.ad_group,
                type=bid_modifiers.BidModifierType.PLACEMENT,
                target=constants.PlacementMedium.APP,
                source=None,
                source_slug="",
                modifier=3.6,
            ),
            magic_mixer.blend(
                bid_modifiers.BidModifier,
                ad_group=self.ad_group,
                type=bid_modifiers.BidModifierType.COUNTRY,
                target=self.us.key,
                source=None,
                source_slug="",
                modifier=2.9,
            ),
            magic_mixer.blend(
                bid_modifiers.BidModifier,
                ad_group=self.ad_group,
                type=bid_modifiers.BidModifierType.STATE,
                target=self.us_tx.key,
                source=None,
                source_slug="",
                modifier=2.4,
            ),
            magic_mixer.blend(
                bid_modifiers.BidModifier,
                ad_group=self.ad_group,
                type=bid_modifiers.BidModifierType.DMA,
                target=self.ep_tx.key,
                source=None,
                source_slug="",
                modifier=0.6,
            ),
            magic_mixer.blend(
                bid_modifiers.BidModifier,
                ad_group=self.ad_group,
                type=bid_modifiers.BidModifierType.AD,
                target=str(self.content_ad.id),
                source=None,
                source_slug="",
                modifier=1.1,
            ),
        ]

        self.bid_modifiers_extra_1 = magic_mixer.blend(
            bid_modifiers.BidModifier,
            ad_group=self.other_ad_group,
            type=bid_modifiers.BidModifierType.PUBLISHER,
            target="example.com",
            source=self.source,
            source_slug=self.source.bidder_slug,
            modifier=3.5,
        )
        self.bid_modifiers_extra_2 = magic_mixer.blend(
            bid_modifiers.BidModifier,
            ad_group=self.other_ad_group,
            type=bid_modifiers.BidModifierType.SOURCE,
            target=str(self.source.id),
            source=None,
            source_slug="",
            modifier=1.1,
        )
        self.bid_modifiers_extra_3 = magic_mixer.blend(
            bid_modifiers.BidModifier,
            ad_group=self.foreign_ad_group,
            type=bid_modifiers.BidModifierType.DEVICE,
            target=str(constants.DeviceType.TV),
            source=None,
            source_slug="",
            modifier=2.1,
        )
        self.bid_modifiers_extra_4 = magic_mixer.blend(
            bid_modifiers.BidModifier,
            ad_group=self.foreign_ad_group,
            type=bid_modifiers.BidModifierType.OPERATING_SYSTEM,
            target=constants.OperatingSystem.WINDOWS,
            source=None,
            source_slug="",
            modifier=0.7,
        )

    def test_list(self):
        response = self.client.get(reverse("adgroups_bidmodifiers_list", kwargs={"ad_group_id": self.ad_group.id}))
        result = self.assertResponseValid(response, status_code=status.HTTP_200_OK, data_type=list)
        self.assertEqual(
            result,
            {
                "count": len(self.bid_modifiers_list),
                "next": None,
                "data": [
                    {
                        "id": str(bm.id),
                        "type": bid_modifiers.BidModifierType.get_name(bm.type),
                        "sourceSlug": bm.source_slug,
                        "target": bid_modifiers.converters.ApiConverter.from_target(bm.type, bm.target),
                        "modifier": bm.modifier,
                    }
                    for bm in self.bid_modifiers_list
                ],
            },
        )

    def test_list_paginated(self):
        response = self.client.get(
            reverse("adgroups_bidmodifiers_list", kwargs={"ad_group_id": self.ad_group.id}),
            {"limit": 2, "marker": self.bid_modifiers_list[3].id},
        )
        result = self.assertResponseValid(response, status_code=status.HTTP_200_OK, data_type=list)
        self.assertEqual(
            result,
            {
                "count": len(self.bid_modifiers_list),
                "next": "http://testserver%s?limit=2&marker=%s"
                % (
                    reverse("adgroups_bidmodifiers_list", kwargs={"ad_group_id": self.ad_group.id}),
                    self.bid_modifiers_list[5].id,
                ),
                "data": [
                    {
                        "id": str(bm.id),
                        "type": bid_modifiers.BidModifierType.get_name(bm.type),
                        "sourceSlug": bm.source_slug,
                        "target": bid_modifiers.converters.ApiConverter.from_target(bm.type, bm.target),
                        "modifier": bm.modifier,
                    }
                    for bm in self.bid_modifiers_list[4:6]
                ],
            },
        )

    def test_list_filter_type(self):
        response = self.client.get(
            reverse("adgroups_bidmodifiers_list", kwargs={"ad_group_id": self.ad_group.id}) + "?type=DEVICE"
        )
        result = self.assertResponseValid(response, status_code=status.HTTP_200_OK, data_type=list)
        bm = self.bid_modifiers_list[2]
        self.assertEqual(
            result,
            {
                "count": 1,
                "next": None,
                "data": [
                    {
                        "id": str(bm.id),
                        "type": bid_modifiers.BidModifierType.get_name(bm.type),
                        "sourceSlug": bm.source_slug,
                        "target": bid_modifiers.converters.ApiConverter.from_target(bm.type, bm.target),
                        "modifier": bm.modifier,
                    }
                ],
            },
        )

    def test_list_filter_illegal_type(self):
        response = self.client.get(
            reverse("adgroups_bidmodifiers_list", kwargs={"ad_group_id": self.ad_group.id}) + "?type=Illegal"
        )
        result = self.assertResponseValid(response, status_code=status.HTTP_200_OK, data_type=list)
        self.assertEqual(result, {"count": 0, "next": None, "data": []})

    def test_list_foreign_ad_group(self):
        response = self.client.get(
            reverse("adgroups_bidmodifiers_list", kwargs={"ad_group_id": self.foreign_ad_group.id})
        )
        result = self.assertResponseValid(response, status_code=status.HTTP_200_OK, data_type=list)
        self.assertEqual(result, {"count": 0, "next": None, "data": []})

    def test_retrieve(self):
        bm = self.bid_modifiers_list[3]
        self._assert_valid_get_response(
            self.ad_group.id,
            bm.id,
            {
                "data": {
                    "id": str(bm.id),
                    "type": bid_modifiers.BidModifierType.get_name(bm.type),
                    "sourceSlug": bm.source_slug,
                    "target": bid_modifiers.converters.ApiConverter.from_target(bm.type, bm.target),
                    "modifier": bm.modifier,
                }
            },
        )

    def test_retrieve_invalid_ad_group(self):
        bm = self.bid_modifiers_list[3]
        response = self._get_bid_modifier_response(self.other_ad_group.id, bm.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        result = self.assertResponseError(response, "MissingDataError")
        self.assertEqual(result, {"errorCode": "MissingDataError", "details": "Bid Modifier does not exist"})

    def test_retrieve_foreign_ad_group_id(self):
        response = self._get_bid_modifier_response(self.foreign_ad_group.id, self.bid_modifiers_extra_3.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        result = self.assertResponseError(response, "MissingDataError")
        self.assertEqual(result, {"errorCode": "MissingDataError", "details": "Bid Modifier does not exist"})

    def test_create(self):
        bm = {
            "type": bid_modifiers.BidModifierType.get_name(bid_modifiers.BidModifierType.PUBLISHER),
            "sourceSlug": self.source.bidder_slug,
            "target": "whatever.com",
            "modifier": 2.5,
        }

        response = self.client.post(
            reverse("adgroups_bidmodifiers_list", kwargs={"ad_group_id": self.ad_group.id}), data=bm, format="json"
        )

        result = self.assertResponseValid(response, status_code=status.HTTP_201_CREATED, data_type=dict)

        bm.update({"id": result["data"]["id"]})

        self.assertEqual(
            result,
            {
                "data": {
                    "id": bm["id"],
                    "type": bm["type"],
                    "sourceSlug": bm["sourceSlug"],
                    "target": bm["target"],
                    "modifier": bm["modifier"],
                }
            },
        )

        self._assert_valid_get_response(
            self.ad_group.id,
            bm["id"],
            {
                "data": {
                    "id": bm["id"],
                    "type": bm["type"],
                    "sourceSlug": bm["sourceSlug"],
                    "target": bm["target"],
                    "modifier": bm["modifier"],
                }
            },
        )

    def test_create_existing(self):
        bm = self.bid_modifiers_list[0]
        data = {
            "type": bid_modifiers.BidModifierType.get_name(bm.type),
            "sourceSlug": bm.source_slug,
            "target": bm.target,
            "modifier": 2.5,
        }

        response = self.client.post(
            reverse("adgroups_bidmodifiers_list", kwargs={"ad_group_id": self.ad_group.id}), data=data, format="json"
        )

        result = self.assertResponseValid(response, status_code=status.HTTP_201_CREATED, data_type=dict)

        self.assertEqual(
            result,
            {
                "data": {
                    "id": str(bm.id),
                    "type": bid_modifiers.BidModifierType.get_name(bm.type),
                    "sourceSlug": bm.source_slug,
                    "target": bm.target,
                    "modifier": 2.5,
                }
            },
        )

    def test_create_foreign_ad_group(self):
        bm = {
            "type": bid_modifiers.BidModifierType.get_name(bid_modifiers.BidModifierType.PUBLISHER),
            "sourceSlug": self.source.bidder_slug,
            "target": "whatever.com",
            "modifier": 2.5,
        }

        response = self.client.post(
            reverse("adgroups_bidmodifiers_list", kwargs={"ad_group_id": self.foreign_ad_group.id}),
            data=bm,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        result = self.assertResponseError(response, "MissingDataError")
        self.assertEqual(result, {"errorCode": "MissingDataError", "details": "Ad Group does not exist"})

    def test_create_missing_slug(self):
        bm = {
            "type": bid_modifiers.BidModifierType.get_name(bid_modifiers.BidModifierType.DEVICE),
            "target": constants.DeviceType.get_name(constants.DeviceType.DESKTOP),
            "modifier": 2.5,
        }

        response = self.client.post(
            reverse("adgroups_bidmodifiers_list", kwargs={"ad_group_id": self.ad_group.id}), data=bm, format="json"
        )

        result = self.assertResponseValid(response, status_code=status.HTTP_201_CREATED, data_type=dict)

        bm.update({"id": result["data"]["id"]})

        self.assertEqual(
            result,
            {
                "data": {
                    "id": bm["id"],
                    "type": bm["type"],
                    "sourceSlug": "",
                    "target": bm["target"],
                    "modifier": bm["modifier"],
                }
            },
        )

        self._assert_valid_get_response(
            self.ad_group.id,
            bm["id"],
            {
                "data": {
                    "id": bm["id"],
                    "type": bm["type"],
                    "sourceSlug": "",
                    "target": bm["target"],
                    "modifier": bm["modifier"],
                }
            },
        )

    def test_create_empty_slug(self):
        bm = {
            "type": bid_modifiers.BidModifierType.get_name(bid_modifiers.BidModifierType.DEVICE),
            "sourceSlug": "",
            "target": constants.DeviceType.get_name(constants.DeviceType.DESKTOP),
            "modifier": 2.5,
        }

        response = self.client.post(
            reverse("adgroups_bidmodifiers_list", kwargs={"ad_group_id": self.ad_group.id}), data=bm, format="json"
        )

        result = self.assertResponseValid(response, status_code=status.HTTP_201_CREATED, data_type=dict)

        bm.update({"id": result["data"]["id"]})

        self.assertEqual(
            result,
            {
                "data": {
                    "id": bm["id"],
                    "type": bm["type"],
                    "sourceSlug": "",
                    "target": bm["target"],
                    "modifier": bm["modifier"],
                }
            },
        )

        self._assert_valid_get_response(
            self.ad_group.id,
            bm["id"],
            {
                "data": {
                    "id": bm["id"],
                    "type": bm["type"],
                    "sourceSlug": "",
                    "target": bm["target"],
                    "modifier": bm["modifier"],
                }
            },
        )

    def test_create_none_slug(self):
        bm = {
            "type": bid_modifiers.BidModifierType.get_name(bid_modifiers.BidModifierType.DEVICE),
            "sourceSlug": None,
            "target": constants.DeviceType.get_name(constants.DeviceType.DESKTOP),
            "modifier": 2.5,
        }

        response = self.client.post(
            reverse("adgroups_bidmodifiers_list", kwargs={"ad_group_id": self.ad_group.id}), data=bm, format="json"
        )

        result = self.assertResponseValid(response, status_code=status.HTTP_201_CREATED, data_type=dict)

        bm.update({"id": result["data"]["id"]})

        self.assertEqual(
            result,
            {
                "data": {
                    "id": bm["id"],
                    "type": bm["type"],
                    "sourceSlug": "",
                    "target": bm["target"],
                    "modifier": bm["modifier"],
                }
            },
        )

        self._assert_valid_get_response(
            self.ad_group.id,
            bm["id"],
            {
                "data": {
                    "id": bm["id"],
                    "type": bm["type"],
                    "sourceSlug": "",
                    "target": bm["target"],
                    "modifier": bm["modifier"],
                }
            },
        )

    def test_create_invalid_modifier_type(self):
        bm = {
            "type": "INVALID",
            "sourceSlug": self.source.bidder_slug,
            "target": "whatever.com",
            "modifier": float(bid_modifiers.helpers.MODIFIER_MAX) + 2.5,
        }

        response = self.client.post(
            reverse("adgroups_bidmodifiers_list", kwargs={"ad_group_id": self.foreign_ad_group.id}),
            data=bm,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        result = self.assertResponseError(response, "ValidationError")
        self.assertEqual(
            result,
            {
                "errorCode": "ValidationError",
                "details": {
                    "modifier": ["Ensure this value is less than or equal to 11.0."],
                    "type": [
                        "Invalid choice INVALID! Valid choices: PUBLISHER, SOURCE, DEVICE, OPERATING_SYSTEM, PLACEMENT, COUNTRY, STATE, DMA, AD"
                    ],
                },
            },
        )

    def test_create_invalid_publisher_domain(self):
        bm = {
            "type": bid_modifiers.BidModifierType.get_name(bid_modifiers.BidModifierType.PUBLISHER),
            "sourceSlug": self.source.bidder_slug,
            "target": "examplecom",
            "modifier": 2.5,
        }

        response = self.client.post(
            reverse("adgroups_bidmodifiers_list", kwargs={"ad_group_id": self.ad_group.id}), data=bm, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        result = self.assertResponseError(response, "ValidationError")
        self.assertEqual(
            result, {"errorCode": "ValidationError", "details": {"nonFieldErrors": ["Invalid domain name"]}}
        )

    def test_create_unsupported_operating_system(self):
        bm = {
            "type": bid_modifiers.BidModifierType.get_name(bid_modifiers.BidModifierType.OPERATING_SYSTEM),
            "sourceSlug": "",
            "target": constants.OperatingSystem.get_name(constants.OperatingSystem.UNKNOWN),
            "modifier": 2.5,
        }

        response = self.client.post(
            reverse("adgroups_bidmodifiers_list", kwargs={"ad_group_id": self.ad_group.id}), data=bm, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        result = self.assertResponseError(response, "ValidationError")
        self.assertEqual(
            result,
            {"errorCode": "ValidationError", "details": {"nonFieldErrors": ["Unsupported Operating System Traget"]}},
        )

    def test_create_invalid_operating_system(self):
        bm = {
            "type": bid_modifiers.BidModifierType.get_name(bid_modifiers.BidModifierType.OPERATING_SYSTEM),
            "sourceSlug": "",
            "target": "invalid",
            "modifier": 2.5,
        }

        response = self.client.post(
            reverse("adgroups_bidmodifiers_list", kwargs={"ad_group_id": self.ad_group.id}), data=bm, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        result = self.assertResponseError(response, "ValidationError")
        self.assertEqual(
            result, {"errorCode": "ValidationError", "details": {"nonFieldErrors": ["Invalid Operating System"]}}
        )

    def test_create_missing_required_slug(self):

        bm = {
            "type": bid_modifiers.BidModifierType.get_name(bid_modifiers.BidModifierType.PUBLISHER),
            "sourceSlug": "",
            "target": "whatever.com",
            "modifier": 2.5,
        }

        response = self.client.post(
            reverse("adgroups_bidmodifiers_list", kwargs={"ad_group_id": self.ad_group.id}), data=bm, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        result = self.assertResponseError(response, "ValidationError")
        self.assertEqual(
            result, {"errorCode": "ValidationError", "details": "Source is required for publisher bid modifier"}
        )

    def test_update(self):
        bm = self.bid_modifiers_list[0]

        response = self.client.put(
            reverse("adgroups_bidmodifiers_details", kwargs={"ad_group_id": self.ad_group.id, "pk": bm.id}),
            data={"modifier": 1.5},
            format="json",
        )

        result = self.assertResponseValid(response, status_code=status.HTTP_200_OK, data_type=dict)

        self.assertEqual(
            result,
            {
                "data": {
                    "id": str(bm.id),
                    "type": bid_modifiers.BidModifierType.get_name(bm.type),
                    "sourceSlug": bm.source_slug,
                    "target": bm.target,
                    "modifier": 1.5,
                }
            },
        )

        self._assert_valid_get_response(
            self.ad_group.id,
            bm.id,
            {
                "data": {
                    "id": str(bm.id),
                    "type": bid_modifiers.BidModifierType.get_name(bm.type),
                    "sourceSlug": bm.source_slug,
                    "target": bm.target,
                    "modifier": 1.5,
                }
            },
        )

    def test_update_invalid_input(self):
        bm = self.bid_modifiers_list[0]

        response = self.client.put(
            reverse("adgroups_bidmodifiers_details", kwargs={"ad_group_id": self.ad_group.id, "pk": bm.id}),
            data={"target": "example.com", "sourceSlug": "some_slug"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        result = self.assertResponseError(response, "ValidationError")
        self.assertEqual(result, {"errorCode": "ValidationError", "details": "Only modifier field can be updated"})

    def test_destroy(self):
        bm = self.bid_modifiers_list[3]

        response = self.client.delete(
            reverse("adgroups_bidmodifiers_details", kwargs={"ad_group_id": self.ad_group.id, "pk": bm.id}),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.content), 0)

        response = self._get_bid_modifier_response(self.ad_group.id, bm.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        result = self.assertResponseError(response, "MissingDataError")
        self.assertEqual(result, {"errorCode": "MissingDataError", "details": "Bid Modifier does not exist"})

        response = self.client.delete(
            reverse("adgroups_bidmodifiers_details", kwargs={"ad_group_id": self.ad_group.id, "pk": bm.id}),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        result = self.assertResponseError(response, "MissingDataError")
        self.assertEqual(result, {"errorCode": "MissingDataError", "details": "Bid Modifier does not exist"})

    def test_destroy_foreign_ad_group(self):
        response = self.client.delete(
            reverse(
                "adgroups_bidmodifiers_details",
                kwargs={"ad_group_id": self.foreign_ad_group.id, "pk": self.bid_modifiers_extra_3.id},
            ),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        result = self.assertResponseError(response, "MissingDataError")
        self.assertEqual(result, {"errorCode": "MissingDataError", "details": "Bid Modifier does not exist"})

    def test_destroy_invalid_bid_modifier_id(self):
        response = self.client.delete(
            reverse(
                "adgroups_bidmodifiers_details",
                kwargs={"ad_group_id": self.foreign_ad_group.id, "pk": self.bid_modifiers_extra_1.id},
            ),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        result = self.assertResponseError(response, "MissingDataError")
        self.assertEqual(result, {"errorCode": "MissingDataError", "details": "Bid Modifier does not exist"})

    def test_destroy_with_data(self):
        bm = self.bid_modifiers_list[3]

        response = self.client.delete(
            reverse("adgroups_bidmodifiers_details", kwargs={"ad_group_id": self.ad_group.id, "pk": bm.id}),
            data={"modifier": 1.5},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        result = self.assertResponseError(response, "ValidationError")
        self.assertEqual(result, {"errorCode": "ValidationError", "details": "Delete Bid Modifier requires no data"})

    def test_destroy_multiple(self):
        response = self.client.delete(
            reverse("adgroups_bidmodifiers_list", kwargs={"ad_group_id": self.ad_group.id}),
            data=[{"id": e.id} for e in self.bid_modifiers_list[:5]],
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.content), 0)

        response = self.client.get(reverse("adgroups_bidmodifiers_list", kwargs={"ad_group_id": self.ad_group.id}))
        result = self.assertResponseValid(response, status_code=status.HTTP_200_OK, data_type=list)
        self.assertEqual(
            result,
            {
                "count": len(self.bid_modifiers_list[5:]),
                "next": None,
                "data": [
                    {
                        "id": str(bm.id),
                        "type": bid_modifiers.BidModifierType.get_name(bm.type),
                        "sourceSlug": bm.source_slug,
                        "target": bm.target,
                        "modifier": bm.modifier,
                    }
                    for bm in self.bid_modifiers_list[5:]
                ],
            },
        )

    def test_destroy_all(self):
        response = self.client.delete(reverse("adgroups_bidmodifiers_list", kwargs={"ad_group_id": self.ad_group.id}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.content), 0)

        response = self.client.get(reverse("adgroups_bidmodifiers_list", kwargs={"ad_group_id": self.ad_group.id}))
        result = self.assertResponseValid(response, status_code=status.HTTP_200_OK, data_type=list)
        self.assertEqual(result, {"count": 0, "next": None, "data": []})

    def test_destroy_multiple_foreign_ad_group(self):
        response = self.client.delete(
            reverse("adgroups_bidmodifiers_list", kwargs={"ad_group_id": self.foreign_ad_group.id}),
            data=[{"id": e.id} for e in self.bid_modifiers_list[:5]],
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        result = self.assertResponseError(response, "ValidationError")
        self.assertEqual(result, {"errorCode": "ValidationError", "details": "Invalid Bid Modifier ids"})

    def test_destroy_multiple_invalid_bid_modifier_id(self):
        response = self.client.delete(
            reverse("adgroups_bidmodifiers_list", kwargs={"ad_group_id": self.ad_group.id}),
            data=[{"id": self.bid_modifiers_extra_1.id}, {"id": self.bid_modifiers_extra_4.id}],
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        result = self.assertResponseError(response, "ValidationError")
        self.assertEqual(result, {"errorCode": "ValidationError", "details": "Invalid Bid Modifier ids"})

    def test_destroy_multiple_wrong_data(self):
        response = self.client.delete(
            reverse("adgroups_bidmodifiers_list", kwargs={"ad_group_id": self.ad_group.id}),
            data=[{"modifier": 1.5}],
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        result = self.assertResponseError(response, "ValidationError")
        self.assertEqual(result, {"errorCode": "ValidationError", "details": [{"id": ["This field is required."]}]})

        response = self.client.delete(
            reverse("adgroups_bidmodifiers_list", kwargs={"ad_group_id": self.ad_group.id}),
            data={"id": self.bid_modifiers_list[0].id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        result = self.assertResponseError(response, "ValidationError")
        self.assertEqual(
            result,
            {
                "errorCode": "ValidationError",
                "details": {"nonFieldErrors": ['Expected a list of items but got type "dict".']},
            },
        )

    def _assert_valid_get_response(self, ad_group_id, pk, expected_json_content, status_code=status.HTTP_200_OK):
        response = self._get_bid_modifier_response(ad_group_id, pk)
        result = self.assertResponseValid(response, status_code=status.HTTP_200_OK, data_type=dict)
        self.assertEqual(result, expected_json_content)

    def _get_bid_modifier_response(self, ad_group_id, pk):
        return self.client.get(reverse("adgroups_bidmodifiers_details", kwargs={"ad_group_id": ad_group_id, "pk": pk}))


class NoPermissionTest(restapi.common.views_base_test.RESTAPITest):
    def setUp(self):
        super(NoPermissionTest, self).setUp()

    def test_list(self):
        response = self.client.get(reverse("adgroups_bidmodifiers_list", kwargs={"ad_group_id": 1}))
        self.assertEqual(response.status_code, 403)
        result = self.assertResponseError(response, "PermissionDenied")
        self.assertEqual(
            result, {"errorCode": "PermissionDenied", "details": "You do not have permission to perform this action."}
        )

    def test_retrieve(self):
        response = self.client.get(reverse("adgroups_bidmodifiers_details", kwargs={"ad_group_id": 1, "pk": 1}))
        self.assertEqual(response.status_code, 403)
        result = self.assertResponseError(response, "PermissionDenied")
        self.assertEqual(
            result, {"errorCode": "PermissionDenied", "details": "You do not have permission to perform this action."}
        )

    def test_create(self):
        response = self.client.post(
            reverse("adgroups_bidmodifiers_list", kwargs={"ad_group_id": 1}), data={}, format="json"
        )
        self.assertEqual(response.status_code, 403)
        result = self.assertResponseError(response, "PermissionDenied")
        self.assertEqual(
            result, {"errorCode": "PermissionDenied", "details": "You do not have permission to perform this action."}
        )

    def test_update(self):
        response = self.client.put(
            reverse("adgroups_bidmodifiers_details", kwargs={"ad_group_id": 1, "pk": 1}), data={}, format="json"
        )
        self.assertEqual(response.status_code, 403)
        result = self.assertResponseError(response, "PermissionDenied")
        self.assertEqual(
            result, {"errorCode": "PermissionDenied", "details": "You do not have permission to perform this action."}
        )

    def test_destroy(self):
        response = self.client.delete(
            reverse("adgroups_bidmodifiers_details", kwargs={"ad_group_id": 1, "pk": 1}), format="json"
        )
        self.assertEqual(response.status_code, 403)
        result = self.assertResponseError(response, "PermissionDenied")
        self.assertEqual(
            result, {"errorCode": "PermissionDenied", "details": "You do not have permission to perform this action."}
        )