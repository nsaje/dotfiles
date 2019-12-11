import core.features.publisher_groups.publisher_group

from . import exceptions


class AccountSettingsValidatorMixin(object):
    MIN_DEFAULT_ICON_SIZE = 128
    MAX_DEFAULT_ICON_SIZE = 10000

    def clean(self, changes):
        self._validate_publisher_groups(changes)
        self._validate_default_icon(changes)

    def _validate_publisher_groups(self, changes):
        whitelist = changes.get("whitelist_publisher_groups")
        blacklist = changes.get("blacklist_publisher_groups")

        if whitelist:
            whitelist_count = (
                core.features.publisher_groups.publisher_group.PublisherGroup.objects.all()
                .filter_by_account(self.account)
                .filter(pk__in=whitelist)
                .count()
            )
            if whitelist_count != len(whitelist):
                raise exceptions.PublisherWhitelistInvalid("Invalid whitelist publisher group selection.")

        if blacklist:
            blacklist_count = (
                core.features.publisher_groups.publisher_group.PublisherGroup.objects.all()
                .filter_by_account(self.account)
                .filter(pk__in=blacklist)
                .count()
            )
            if blacklist_count != len(blacklist):
                raise exceptions.PublisherBlacklistInvalid("Invalid blacklist publisher group selection.")

    def _validate_default_icon(self, changes):
        default_icon = changes.get("default_icon")
        if not default_icon:
            return

        if default_icon.width != default_icon.height:
            raise exceptions.DefaultIconNotSquare("Image height and width must be equal.")

        if default_icon.width < self.MIN_DEFAULT_ICON_SIZE:
            raise exceptions.DefaultIconTooSmall(
                "Image too small (minimum size is {min}x{min} px).".format(min=self.MIN_DEFAULT_ICON_SIZE)
            )

        if default_icon.width > self.MAX_DEFAULT_ICON_SIZE:
            raise exceptions.DefaultIconTooBig(
                "Image too big (maximum size is {max}x{max} px).".format(max=self.MAX_DEFAULT_ICON_SIZE)
            )
