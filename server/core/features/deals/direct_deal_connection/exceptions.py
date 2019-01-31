from utils.exc import ValidationError


class CannotSetExclusiveAndGlobal(ValidationError):
    pass


class CannotSetMultipleEntities(ValidationError):
    pass


class DealAlreadyUsedAsGlobalDeal(ValidationError):
    pass
