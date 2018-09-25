from utils.exc import ValidationError


class CampaignTypesDoNotMatch(ValidationError):
    pass


class CannotChangeBiddingType(ValidationError):
    pass
