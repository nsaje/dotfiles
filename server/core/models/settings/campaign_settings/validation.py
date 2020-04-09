import core.features.publisher_groups

from . import exceptions


class CampaignSettingsValidatorMixin(object):
    def clean(self, changes):
        self._validate_language(changes)
        self._validate_publisher_groups(changes)

    def _validate_language(self, changes):
        if "language" in changes and self.campaign.adgroup_set.count() > 0:
            msg = "Cannot change language because Campaign has Ad Group/Ad Groups"
            raise exceptions.CannotChangeLanguage(msg)

    def _validate_publisher_groups(self, changes):
        whitelist = changes.get("whitelist_publisher_groups")
        blacklist = changes.get("blacklist_publisher_groups")

        if whitelist:
            whitelist_count = (
                core.features.publisher_groups.PublisherGroup.objects.all()
                .filter_by_account(self.campaign.account)
                .filter(pk__in=whitelist)
                .count()
            )
            if whitelist_count != len(whitelist):
                raise exceptions.PublisherWhitelistInvalid("Invalid whitelist publisher group selection.")

        if blacklist:
            blacklist_count = (
                core.features.publisher_groups.PublisherGroup.objects.all()
                .filter_by_account(self.campaign.account)
                .filter(pk__in=blacklist)
                .count()
            )
            if blacklist_count != len(blacklist):
                raise exceptions.PublisherBlacklistInvalid("Invalid blacklist publisher group selection.")
