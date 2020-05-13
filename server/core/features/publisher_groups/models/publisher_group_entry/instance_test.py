from django.test import TestCase

import dash.models
from utils.magic_mixer import magic_mixer


class EmptyPlacementTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.account = magic_mixer.blend(dash.models.Account)
        self.publisher_group = magic_mixer.blend(dash.models.PublisherGroup, account=self.account)
        self.source = magic_mixer.blend(dash.models.Source)
        self.publisher = "example.com"

    def test_save_single(self):
        with self.assertRaises(ValueError) as e:
            instance = dash.models.PublisherGroupEntry(
                publisher_group=self.publisher_group, source=self.source, publisher=self.publisher, placement=""
            )
            instance.save()
        self.assertEqual(str(e.exception), "Placement must not be empty")

    def test_create_single(self):
        with self.assertRaises(ValueError) as e:
            dash.models.PublisherGroupEntry.objects.create(
                publisher_group=self.publisher_group, source=self.source, publisher=self.publisher, placement=""
            )
        self.assertEqual(str(e.exception), "Placement must not be empty")

    def test_create_bulk(self):
        with self.assertRaises(ValueError) as e:
            instances = [
                dash.models.PublisherGroupEntry(
                    publisher_group=self.publisher_group, source=self.source, publisher=self.publisher, placement=""
                )
            ]
            dash.models.PublisherGroupEntry.objects.bulk_create(instances)
            self.assertEqual(str(e.exception), "Placement must not be empty")
