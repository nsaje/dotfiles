import core.publisher_groups.publisher_group

from . import exceptions


class AccountSettingsValidatorMixin(object):
    def clean(self, changes):
        self._validate_publisher_groups(changes)

    def _validate_publisher_groups(self, changes):
        whitelist = changes.get("whitelist_publisher_groups")
        blacklist = changes.get("blacklist_publisher_groups")

        if whitelist:
            whitelist_count = (
                core.publisher_groups.publisher_group.PublisherGroup.objects.all()
                .filter_by_account(self.account)
                .filter(pk__in=whitelist)
                .count()
            )
            if whitelist_count != len(whitelist):
                raise exceptions.PublisherWhitelistInvalid("Invalid whitelist publisher group selection.")

        if blacklist:
            blacklist_count = (
                core.publisher_groups.publisher_group.PublisherGroup.objects.all()
                .filter_by_account(self.account)
                .filter(pk__in=blacklist)
                .count()
            )
            if blacklist_count != len(blacklist):
                raise exceptions.PublisherBlacklistInvalid("Invalid blacklist publisher group selection.")
