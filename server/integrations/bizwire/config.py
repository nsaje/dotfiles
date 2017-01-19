from decimal import Decimal
from dash import constants

AUTOMATION_CAMPAIGN = 1096
AUTOMATION_USER_EMAIL = 'businesswire-user@zemanta.com'

DEFAULT_CPC = Decimal('0.2')
DAILY_BUDGET_INITIAL = 10  # initial daily budget - increases as articles start importing
DAILY_BUDGET_PER_ARTICLE = 3.25

INTEREST_TARGETING = [
    constants.InterestCategory.ENTERTAINMENT,
    constants.InterestCategory.FUN_QUIZZES,
    constants.InterestCategory.POLITICS_LAW,
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
    constants.InterestCategory.UTILITY,
    constants.InterestCategory.PREMIUM,
]

NOTIFICATION_EMAILS = [
    'luka.silovinac@zemanta.com',
    'tadej.pavlic@zemanta.com',
    # 'bostjan@zemanta.com',
]
