from utils.exc import ValidationError


class CampaignAdTypeMismatch(ValidationError):
    pass


class AdGroupIsArchived(ValidationError):
    pass
