
from . import exceptions


class CampaignValidatorMixin(object):
    def _validate_type(self, type):
        if self.type != type and self.adgroup_set.count() > 0:
            msg = "Cannot change type because Campaign has Ad Group/Ad Groups"
            raise exceptions.CannotChangeType(msg)
