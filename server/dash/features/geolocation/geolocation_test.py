from django.test import TestCase
from mixer.backend.django import mixer

import dash.constants

from . import geolocation


class GeolocationTestCase(TestCase):
    def test_key_in(self):
        """ Geolocation should return a subset of location objects filtered by key """
        keys = ["a", "b", "c"]
        mixer.cycle(3).blend(geolocation.Geolocation, key=(key for key in keys))
        mixer.cycle(5).blend(geolocation.Geolocation, key=mixer.sequence("unmatched_{0}"))
        self.assertEqual(len(geolocation.Geolocation.objects.all()), 8)
        self.assertEqual(len(geolocation.Geolocation.objects.key_in(keys)), 3)

    def test_of_type(self):
        """ Geolocation should return a subset of location objects filtered by type """
        types = [dash.constants.LocationType.COUNTRY, dash.constants.LocationType.REGION]
        mixer.cycle(3).blend(geolocation.Geolocation, type=dash.constants.LocationType.COUNTRY)
        mixer.cycle(3).blend(geolocation.Geolocation, type=dash.constants.LocationType.REGION)
        mixer.cycle(2).blend(geolocation.Geolocation, type=dash.constants.LocationType.CITY)
        mixer.cycle(2).blend(geolocation.Geolocation, type=dash.constants.LocationType.DMA)
        mixer.cycle(2).blend(geolocation.Geolocation, type=dash.constants.LocationType.ZIP)
        self.assertEqual(len(geolocation.Geolocation.objects.all()), 12)
        self.assertEqual(len(geolocation.Geolocation.objects.of_type(types)), 6)

    def test_name_contains(self):
        """ Geolocation should return a subset of location objects filtered by name """
        mixer.cycle(4).blend(geolocation.Geolocation, name=mixer.sequence("Location Matched {0}"))
        mixer.cycle(2).blend(geolocation.Geolocation, name=mixer.sequence("Location Unmatched {0}"))
        self.assertEqual(len(geolocation.Geolocation.objects.all()), 6)
        self.assertEqual(len(geolocation.Geolocation.objects.name_contains("ion mat")), 4)

    def test_name_contains_accents(self):
        """ Geolocation should return a subset of location objects filtered by name (accented characters match) """
        mixer.blend(geolocation.Geolocation, name="Dvůr Králové nad Labem")
        mixer.blend(geolocation.Geolocation, name="Český Těšín")
        mixer.blend(geolocation.Geolocation, name="Hyōgo")
        mixer.blend(geolocation.Geolocation, name="Saarbrücken")
        mixer.blend(geolocation.Geolocation, name="Español")
        mixer.blend(geolocation.Geolocation, name="Cádiz")

        self.assertEqual(len(geolocation.Geolocation.objects.name_contains("dvur kralove")), 1)
        self.assertEqual(len(geolocation.Geolocation.objects.name_contains("cesky tesin")), 1)
        self.assertEqual(len(geolocation.Geolocation.objects.name_contains("hyo")), 1)
        self.assertEqual(len(geolocation.Geolocation.objects.name_contains("bruck")), 1)
        self.assertEqual(len(geolocation.Geolocation.objects.name_contains("espanol")), 1)
        self.assertEqual(len(geolocation.Geolocation.objects.name_contains("cad")), 1)

    def test_search(self):
        """ Geolocation should return a subset of location objects when searching by key, type and/ or name """
        params = {
            "keys": ["a", "b"],
            "types": [
                dash.constants.LocationType.COUNTRY,
                dash.constants.LocationType.REGION,
                dash.constants.LocationType.CITY,
            ],
            "name_contains": "A",
        }
        mixer.blend(geolocation.Geolocation, key="a", type=dash.constants.LocationType.COUNTRY, name="A")
        mixer.blend(geolocation.Geolocation, key="b", type=dash.constants.LocationType.REGION, name="B")
        mixer.blend(geolocation.Geolocation, key="x", type=dash.constants.LocationType.CITY, name="X")
        mixer.cycle(20).blend(geolocation.Geolocation, key=mixer.sequence("unmatched_{0}"), type="x", name="R")

        self.assertEqual(len(geolocation.Geolocation.objects.search(keys=params["keys"])), 2)
        self.assertEqual(len(geolocation.Geolocation.objects.search(types=params["types"])), 3)
        self.assertEqual(len(geolocation.Geolocation.objects.search(name_contains=params["name_contains"])), 1)
        self.assertEqual(len(geolocation.Geolocation.objects.search(limit=15)), 15)
        self.assertEqual(len(geolocation.Geolocation.objects.search(**params)), 1)
        self.assertEqual(len(geolocation.Geolocation.objects.search(offset=10)), 13)
        self.assertEqual(len(geolocation.Geolocation.objects.search(offset=10, limit=8)), 8)
