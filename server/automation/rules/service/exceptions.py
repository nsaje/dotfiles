from utils.exc import ValidationError


class ApplyFailedBase(ValidationError):
    pass


class CampaignAutopilotActive(ApplyFailedBase):
    pass


class BudgetAutopilotInactive(ApplyFailedBase):
    pass


class RuleArchived(ApplyFailedBase):
    pass


class NoCPAGoal(ValidationError):
    pass
