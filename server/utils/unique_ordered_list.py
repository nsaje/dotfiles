class UniqueOrderedList(object):

    class Item(object):
        def __init__(self, value):
            self.value = value
            self.previous = None
            self.next = None

        def __str__(self):
            return "{value: %s, previous: %s, next: %s}" % (
                self.value, self.previous.value if self.previous else 'None',
                self.next.value if self.next else 'None')

        def __repr__(self):
            return self.__str__()

    def __init__(self):
        self._first = None
        self._last = None
        self._map = dict()

    def _add_item_to_end(self, item):
        item.previous = self._last
        item.next = None
        if self._last:
            self._last.next = item
        self._last = item
        if not self._first:
            self._first = item

    def _delete_item(self, item):
        previous = item.previous
        nxt = item.next
        if previous:
            previous.next = nxt
        if nxt:
            nxt.previous = previous
        if self._first == item:
            self._first = nxt
        if self._last == item:
            self._last = previous

    def add_or_move_to_end(self, value):
        item = self._map.get(value)
        if item:
            self._delete_item(item)
        else:
            item = self.Item(value)
            self._map[value] = item
        self._add_item_to_end(item)

    def __iter__(self):
        current = self._first
        while current:
            yield current.value
            current = current.next

    def __reversed__(self):
        current = self._last
        while current:
            yield current.value
            current = current.previous
