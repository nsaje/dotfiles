import datetime
from decimal import Decimal

from dash import constants

START_DATE = datetime.date(2016, 12, 3)

AUTOMATION_CAMPAIGN = 1096
AUTOMATION_USER_EMAIL = "businesswire-user@zemanta.com"

DEFAULT_CPC = Decimal("0.16")
DAILY_BUDGET_RTB_INITIAL = 30
DAILY_BUDGET_OB_INITIAL = 10
DAILY_BUDGET_PER_ARTICLE = 3.375

OB_DAILY_BUDGET_PCT = 0  # 0.1

CUSTOM_CPC_SETTINGS = {3: Decimal("0.2")}

INTEREST_TARGETING = [
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
    "luka.silovinac@zemanta.com",
    "tadej.pavlic@zemanta.com",
    "prodops@outbrain.com",
    # 'bostjan@zemanta.com',
    "tfischer@outbrain.com",
]
