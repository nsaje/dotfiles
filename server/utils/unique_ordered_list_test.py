from django.test import TestCase

from . import unique_ordered_list


class UniqueOrderedListTest(TestCase):

    def test_behaviour(self):
        uol = unique_ordered_list.UniqueOrderedList()
        uol.add_or_move_to_end(1)
        uol.add_or_move_to_end(2)
        uol.add_or_move_to_end(3)
        uol.add_or_move_to_end(4)
        uol.add_or_move_to_end(1)
        uol.add_or_move_to_end(2)
        uol.add_or_move_to_end(3)
        uol.add_or_move_to_end(4)
        uol.add_or_move_to_end(2)
        uol.add_or_move_to_end(1)
        self.assertEqual(list(uol), [3, 4, 2, 1])
        self.assertEqual(list(reversed(uol)), [1, 2, 4, 3])
