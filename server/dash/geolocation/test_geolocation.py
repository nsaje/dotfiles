from django.test import TestCase
from mixer.backend.django import mixer

import geolocation


class GeolocationTestCase(TestCase):
    def test_map(self):
        """ Geolocation map should return a subset of location objects filtered by key """
        keys = ['a', 'b', 'c']
        mixer.cycle(3).blend(geolocation.Geolocation, key=(key for key in keys))
        mixer.cycle(5).blend(geolocation.Geolocation, key=mixer.sequence('unmatched_{0}'))
        self.assertEqual(len(geolocation.Geolocation.objects.all()), 8)
        self.assertEqual(len(geolocation.Geolocation.objects.map(keys)), 3)

    def test_search(self):
        """ Geolocation search should return a subset of location objects filtered by name """
        mixer.cycle(4).blend(geolocation.Geolocation, name=mixer.sequence('Location Matched {0}'))
        mixer.cycle(2).blend(geolocation.Geolocation, name=mixer.sequence('Location Unmatched {0}'))
        self.assertEqual(len(geolocation.Geolocation.objects.all()), 6)
        self.assertEqual(len(geolocation.Geolocation.objects.search('ion mat')), 4)
