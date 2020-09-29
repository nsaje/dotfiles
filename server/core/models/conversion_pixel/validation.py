import core.features.audiences

from . import exceptions
from . import model


class ConversionPixelValidatorMixin(object):
    def clean(self, changes):
        self._validate_name(changes)
        self._validate_archived(changes)

    def _validate_name(self, changes):
        if "name" not in changes:
            return

        if self.pk:
            # NOTE: intentional since name is copied into goal name and changing it would result in inconsistencies
            raise exceptions.PixelNameNotEditable("Pixel name can't be updated")

        if model.ConversionPixel.objects.filter(account=self.account, name=changes["name"]).exists():
            raise exceptions.DuplicatePixelName("Conversion pixel with name {} already exists.".format(changes["name"]))

    def _validate_archived(self, changes):
        if changes.get("archived"):
            non_archived_audiences = core.features.audiences.Audience.objects.filter(pixel=self.id, archived=False)
            if len(non_archived_audiences):
                raise exceptions.AudiencePixelCanNotBeArchived("Can not archive pixel used in non-archived audiences.")
