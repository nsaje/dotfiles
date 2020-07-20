from utils.exc import ValidationError


class ApplyFailedBase(ValidationError):
    pass


class CampaignAutopilotActive(ApplyFailedBase):
    pass


class BudgetAutopilotInactive(ApplyFailedBase):
    pass
