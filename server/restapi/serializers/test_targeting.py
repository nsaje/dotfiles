from django.test import TestCase

import targeting
from utils.magic_mixer import magic_mixer


class PlacementsSerializerTests(TestCase):
    def test_serialization(self):
        data = ['app', 'site']
        serializer = targeting.PlacementsSerializer(data)
        self.assertEqual(serializer.data, ['APP', 'SITE'])

    def test_serialization_with_none(self):
        serializer = targeting.PlacementsSerializer(None)
        self.assertEqual(serializer.data, [])

    def test_deserialization(self):
        data = ['APP', 'SITE']
        serializer = targeting.PlacementsSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data, ['app', 'site'])


class DevicesSerializerTests(TestCase):
    def test_serialization(self):
        data = ['mobile', 'desktop']
        serializer = targeting.DevicesSerializer(data)
        self.assertEqual(serializer.data, ['MOBILE', 'DESKTOP'])

    def test_serialization_with_none(self):
        serializer = targeting.DevicesSerializer(None)
        self.assertEqual(serializer.data, [])

    def test_deserialization(self):
        data = ['MOBILE', 'DESKTOP']
        serializer = targeting.DevicesSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data, ['mobile', 'desktop'])


class OsSerializerTests(TestCase):
    def test_deserialization(self):
        data = {
            'name': 'IOS',
            'version': {
                'min': 'IOS_8_0',
                'max': 'IOS_9_0',
            }
        }
        serializer = targeting.OSSerializer(data=data)
        serializer.is_valid()
        self.assertEqual(
            serializer.validated_data,
            {
                'name': 'ios',
                'version': {
                    'min': 'ios_8_0',
                    'max': 'ios_9_0',
                }
            }
        )

    def test_serialization(self):
        data = {
            'name': 'ios',
            'version': {
                'min': 'ios_8_0',
                'max': 'ios_9_0',
            }
        }
        serializer = targeting.OSSerializer(data)
        self.assertEqual(
            serializer.data,
            {
                'name': 'IOS',
                'version': {
                    'min': 'IOS_8_0',
                    'max': 'IOS_9_0',
                }
            }
        )

    def test_validation_version_missmatch(self):
        data = {
            'name': 'IOS',
            'version': {
                'min': 'IOS_9_0',
                'max': 'IOS_8_0',
            }
        }

        serializer = targeting.OSSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_validation_compatibility(self):
        data = {
            'name': 'IOS',
            'version': {
                'min': 'WINDOWS_XP',
                'max': 'IOS_8_0',
            }
        }

        serializer = targeting.OSSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_no_version(self):
        data = {
            'name': 'IOS',
        }

        serializer = targeting.OSSerializer(data=data)
        self.assertTrue(serializer.is_valid())


class DemographicSerializerTests(TestCase):

    def setUp(self):
        self.serialized = {
            'AND': [
                {
                    'OR': [
                        {'category': 'bluekai:12345'},
                        {'category': 'lotame:23456'},
                        {'category': 'lr-test:34567'},
                    ]
                }, {
                    'OR': [
                        {'category': 'outbrain:45678'},
                        {'category': 'lotame:56789'},
                    ]
                }, {
                    'NOT': [
                        {'category': 'bluekai:98765'},
                    ]
                }]
        }
        self.deserialized = [
            'and',
            ['or', 'bluekai:12345', 'lotame:23456', 'lr-test:34567'],
            ['or', 'outbrain:45678', 'lotame:56789'],
            ['not', 'bluekai:98765']]

    def test_deserialization(self):
        data = self.serialized
        serializer = targeting.DemographicSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data,
            self.deserialized)

    def test_serialization(self):
        request = magic_mixer.blend_request_user(
            permissions=['can_use_bluekai_targeting'])
        data = self.deserialized
        serializer = targeting.DemographicSerializer(
            data, context={'request': request})
        self.assertEqual(serializer.data, self.serialized)

    def test_serialization_with_list(self):
        data = self.deserialized
        serializer = targeting.DemographicSerializer(data)
        self.assertEqual(serializer.data, data)

    def test_serialization_error(self):
        data = {
            'AND': [
                {
                    'XOR': [
                        {'category': '12345'},
                        {'category': '23456'},
                        {'category': '34567'},
                    ]
                }]
        }
        serializer = targeting.DemographicSerializer(data=data)
        self.assertFalse(serializer.is_valid())
