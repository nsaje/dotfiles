from django.test import TestCase

from utils.magic_mixer import magic_mixer

from . import model


class PublisherGroupManagerTest(TestCase):
    def test_delete(self):
        magic_mixer.blend(model.PublisherGroup)
        with self.assertRaises(AssertionError):
            model.PublisherGroup.objects.delete()
