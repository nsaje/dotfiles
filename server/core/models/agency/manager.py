import core.common
import core.models

from . import model


class AgencyManager(core.common.BaseManager):
    def create(self, request, name, **kwargs):
        agency = model.Agency(name=name, **kwargs)
        agency.save(request)

        agency.settings = core.models.settings.AgencySettings(agency=agency)
        agency.settings.update(request)
        agency.settings_id = agency.settings.id
        agency.save(request)

        return agency
