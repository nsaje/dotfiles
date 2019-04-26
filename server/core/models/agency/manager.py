import core.common
import core.models
from prodops import hacks

from . import model


class AgencyManager(core.common.BaseManager):
    def create(self, request, name, **kwargs):
        agency = model.Agency(name=name)
        agency.save(request)
        if request is not None:
            # TODO: tfischer 25/04/2019 Will be moved to salesforce as soon as the Ligatus integration is finished.
            hacks.add_agency_default_amplify_settings(request.user, kwargs)
        agency.update(request, **kwargs)
        agency.settings = core.models.settings.AgencySettings(agency=agency)
        agency.settings.update(request)
        agency.settings_id = agency.settings.id
        agency.save(request)

        return agency
