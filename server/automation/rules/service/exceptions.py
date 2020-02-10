from utils.exc import ValidationError


class CampaignAutopilotActive(ValidationError):
    pass


class BudgetAutopilotInactive(ValidationError):
    pass


class AutopilotActive(ValidationError):
    pass
