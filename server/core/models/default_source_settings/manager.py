import core.common

from . import queryset


class DefaultSourceSettingsManager(core.common.BaseManager):
    def get_queryset(self):
        return queryset.DefaultSourceSettingsQuerySet(self.model)
