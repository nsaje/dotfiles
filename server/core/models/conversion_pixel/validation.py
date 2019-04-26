from . import exceptions
from . import model


class ConversionPixelValidatorMixin(object):
    def clean(self, changes):
        self._validate_flags(changes)
        self._validate_name(changes)
        self._validate_archived(changes)

    def _validate_flags(self, changes):
        audience_pixel = changes.get("audience_enabled", self.audience_enabled)
        additional_pixel = changes.get("additional_pixel", self.additional_pixel)

        if not audience_pixel and not additional_pixel:
            return

        if audience_pixel and additional_pixel:
            raise exceptions.MutuallyExclusivePixelFlagsEnabled(
                "Custom audience and additional audience can not be enabled at the same time on the same pixel."
            )

        audience_pixels = model.ConversionPixel.objects.filter(
            account_id=self.account.id, audience_enabled=True
        ).exclude(pk=self.id)

        if audience_pixel and audience_pixels.exists():
            raise exceptions.AudiencePixelAlreadyExists(
                "This pixel can not be used for building custom audiences because another pixel is already used: {}.".format(
                    audience_pixels.first().name
                )
            )

        elif additional_pixel and not audience_pixels.exists():
            raise exceptions.AudiencePixelNotSet(
                "The pixel's account has no audience pixel set. Set an audience pixel before setting an additional audience pixel."
            )

    def _validate_name(self, changes):
        if "name" not in changes:
            return

        if self.pk:
            # NOTE: intentional since name is copied into goal name and changing it would result in inconsistencies
            raise exceptions.PixelNameNotEditable("Pixel name can't be updated")

        if model.ConversionPixel.objects.filter(account=self.account, name=changes["name"]).exists():
            raise exceptions.DuplicatePixelName("Conversion pixel with name {} already exists.".format(changes["name"]))

    def _validate_archived(self, changes):
        if changes.get("archived") and (
            changes.get("audience_enabled", self.audience_enabled)
            or changes.get("additional_pixel", self.additional_pixel)
        ):
            raise exceptions.AudiencePixelCanNotBeArchived("Can not archive pixel used for building custom audiences.")
