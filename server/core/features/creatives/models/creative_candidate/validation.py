import dash.constants

from ... import converters
from . import exceptions


class CreativeCandidateValidatorMixin(object):
    def clean(self):
        super().clean()
        self._validate_batch_status()
        self._validate_type()

    def _validate_batch_status(self):
        if self.batch.status != dash.constants.CreativeBatchStatus.IN_PROGRESS:
            raise exceptions.BatchStatusInvalid()

    def _validate_type(self):
        if self.batch.type != converters.ConstantsConverter.to_batch_type(self.type):
            raise exceptions.AdTypeInvalid()
