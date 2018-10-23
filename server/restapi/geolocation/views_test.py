from django.urls import reverse

import restapi.common.views_base_test


class GeolocationListViewTest(restapi.common.views_base_test.RESTAPITest):
    def test_get_with_no_filter(self):
        r = self.client.get(reverse("geolocation_list"))
        r = self.assertResponseValid(r, data_type=list)
        self.assertEqual(len(r["data"]), 10)

    def test_get_with_keys_filter(self):
        keys = ["US", "GB"]
        r = self.client.get(reverse("geolocation_list") + "?keys=US,GB")
        r = self.assertResponseValid(r, data_type=list)
        self.assertFalse(any(location["key"] not in keys for location in r["data"]))

    def test_get_with_types_filter(self):
        types = ["COUNTRY", "CITY"]
        r = self.client.get(reverse("geolocation_list") + "?types=COUNTRY,CITY")
        r = self.assertResponseValid(r, data_type=list)
        self.assertFalse(any(location["type"] not in types for location in r["data"]))

    def test_get_with_name_contains_filter(self):
        r = self.client.get(reverse("geolocation_list") + "?nameContains=New")
        r = self.assertResponseValid(r, data_type=list)
        self.assertFalse(any("New" not in location["name"] for location in r["data"]))

    def test_get_with_types_and_name_contains_filter(self):
        types = ["COUNTRY", "CITY"]
        r = self.client.get(reverse("geolocation_list") + "?types=COUNTRY,CITY&nameContains=New")
        r = self.assertResponseValid(r, data_type=list)
        self.assertFalse(any(location["type"] not in types or "New" not in location["name"] for location in r["data"]))
