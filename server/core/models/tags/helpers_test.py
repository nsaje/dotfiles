from django import test

from utils.magic_mixer import magic_mixer

from . import EntityTag
from . import helpers


class EntityTagHelpersTestCase(test.TestCase):
    def setUp(self):
        self.tag_names = [
            "test",
            "other",
            "sth",
            "sth/tag_13",
            "other/tag_14",
            "test/tag_16",
            "sth/tag_15",
            "test/tag_6",
            "test/tag_11",
            "other/tag_3",
            "other/tag_7",
            "test/tag_4",
            "sth/tag_10",
            "test/tag_2",
            "other/tag_12",
            "sth/tag_5",
            "sth/tag_8",
            "test/tag_1",
            "test/tag_9",
        ]
        self.expected_string = "other,other/tag_12,other/tag_14,other/tag_3,other/tag_7,sth,sth/tag_10,sth/tag_13,sth/tag_15,sth/tag_5,sth/tag_8,test,test/tag_1,test/tag_11,test/tag_16,test/tag_2,test/tag_4,test/tag_6,test/tag_9"
        magic_mixer.cycle(len(self.tag_names)).blend(EntityTag, name=(name for name in self.tag_names))

    def test_entity_tag_names_to_string_none(self):
        self.assertEqual(helpers.entity_tag_names_to_string(None), "")

    def test_entity_tag_names_to_string_empty(self):
        self.assertEqual(helpers.entity_tag_names_to_string([]), "")

    def test_entity_tag_names_to_string_names(self):
        self.assertEqual(helpers.entity_tag_names_to_string(self.tag_names), self.expected_string)

    def test_tag_query_set_to_string_no_tags(self):
        self.assertEqual(helpers.entity_tag_query_set_to_string(EntityTag.objects.none()), "")

    def test_tag_query_set_to_string_with_tags(self):
        self.assertEqual(helpers.entity_tag_query_set_to_string(EntityTag.objects.all()), self.expected_string)
