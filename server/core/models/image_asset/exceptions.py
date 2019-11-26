from utils.exc import ValidationError


class ImageAssetExternalValidationFailed(ValidationError):
    pass


class ImageAssetInvalid(ValidationError):
    pass
