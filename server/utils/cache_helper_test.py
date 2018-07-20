from django.test import TestCase

from dash import models
from stats.helpers import Goals
from utils.magic_mixer import magic_mixer

from .cache_helper import get_cache_key


class C(object):
    def __init__(self, v):
        self.v = v


class CacheHelperTest(TestCase):
    def test_queryset(self):
        magic_mixer.cycle(3).blend(models.CampaignGoal)

        self.assertEqual(
            get_cache_key(models.CampaignGoal.objects.all()), get_cache_key(models.CampaignGoal.objects.all())
        )
        self.assertNotEqual(
            get_cache_key(models.CampaignGoal.objects.all()), get_cache_key(models.CampaignGoal.objects.none())
        )

    def test_model(self):
        goal1 = magic_mixer.blend(models.CampaignGoal)
        goal2 = magic_mixer.blend(models.CampaignGoal)

        self.assertEqual(get_cache_key(goal1), get_cache_key(goal1))
        self.assertNotEqual(get_cache_key(goal1), get_cache_key(goal2))

    def test_namedtuple(self):
        goals1 = Goals(1, 2, 3, 4, 5)
        goals2 = Goals(5, 4, 3, 2, 1)

        self.assertEqual(get_cache_key(goals1), get_cache_key(goals1))
        self.assertNotEqual(get_cache_key(goals1), get_cache_key(goals2))

    def test_class(self):
        c1 = C(1)
        c2 = C(2)

        self.assertEqual(get_cache_key(c1), get_cache_key(c1))
        self.assertNotEqual(get_cache_key(c1), get_cache_key(c2))

    def test_dict(self):
        self.assertEqual(get_cache_key({1: 1, 9: 9}), get_cache_key({9: 9, 1: 1}))
        self.assertNotEqual(get_cache_key({1: 1}), get_cache_key({1: 2}))
        self.assertNotEqual(get_cache_key({1: 1}), get_cache_key({2: 1}))

    def test_str(self):
        self.assertEqual(get_cache_key("abc"), get_cache_key("abc"))
        self.assertNotEqual(get_cache_key("abc"), get_cache_key("abd"))

    def test_list(self):
        self.assertEqual(get_cache_key([1, 2]), get_cache_key([1, 2]))
        self.assertNotEqual(get_cache_key([1, 2]), get_cache_key([2, 3]))

    def test_multiple(self):
        self.assertEqual(get_cache_key(1, 2, a=3), get_cache_key(1, 2, a=3))
        self.assertNotEqual(get_cache_key(1, 2, a=3), get_cache_key(1, 3, a=3))
        self.assertNotEqual(get_cache_key(1, 2, a=3), get_cache_key(1, 2, a=4))

    def test_hierarchy(self):
        a = [{"a": 1, "b": {"c": 2, "d": [1, 3]}}]
        b = [{"a": 1, "b": {"c": 2, "d": [1, 4]}}]
        self.assertEqual(get_cache_key(a), get_cache_key(a))
        self.assertNotEqual(get_cache_key(a), get_cache_key(b))
