from decimal import Decimal
from dash import constants

AUTOMATION_CAMPAIGN = 1096
AUTOMATION_USER_EMAIL = 'businesswire-user@zemanta.com'

DEFAULT_CPC = Decimal('0.2')
DEFAULT_DAILY_BUDGET = 25  # initial daily budget - increases as articles start importing

INTEREST_TARGETING = [
    constants.InterestCategory.ENTERTAINMENT,
    constants.InterestCategory.FUN,
    constants.InterestCategory.POLITICS,
    constants.InterestCategory.FASHION,
    constants.InterestCategory.FINANCE,
    constants.InterestCategory.MEDIA,
    constants.InterestCategory.RELIGION,
    constants.InterestCategory.WEATHER,
    constants.InterestCategory.PETS,
    constants.InterestCategory.HOME,
    constants.InterestCategory.WOMEN,
    constants.InterestCategory.FAMILY,
    constants.InterestCategory.FOOD,
    constants.InterestCategory.SCIENCE,
    constants.InterestCategory.HOBBIES,
    constants.InterestCategory.MUSIC,
    constants.InterestCategory.TECHNOLOGY,
    constants.InterestCategory.EDUCATION,
    constants.InterestCategory.TRAVEL,
    constants.InterestCategory.MEN,
    constants.InterestCategory.CARS,
    constants.InterestCategory.SPORTS,
    constants.InterestCategory.HEALTH,
    constants.InterestCategory.LAW,
    constants.InterestCategory.UTILITY,
    constants.InterestCategory.PREMIUM,
]

NOTIFICATION_EMAILS = [
    'luka.silovinac@zemanta.com',
    'tadej.pavlic@zemanta.com',
    # 'bostjan@zemanta.com',
]
