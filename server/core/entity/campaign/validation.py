
from . import exceptions


class CampaignValidatorMixin(object):
    def _validate_type(self, type):
        if self.type != type and self.adgroup_set.count() > 0:
            msg = "Cannot set type for campaign with ad groups"
            raise exceptions.CannotChangeType(msg)
