# -*- coding: utf-8 -*-

import base_manager


class QuerySetManager(base_manager.BaseManager):

    def get_queryset(self):
        return self.model.QuerySet(self.model)
