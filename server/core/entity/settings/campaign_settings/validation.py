from .exceptions import CannotChangeLanguage


class CampaignSettingsValidatorMixin(object):

    def clean(self, changes):
        if 'language' in changes and self.campaign.adgroup_set.count() > 0:
            msg = 'Cannot change language because Campaign has Ad Group/Ad Groups'
            raise CannotChangeLanguage(msg)
