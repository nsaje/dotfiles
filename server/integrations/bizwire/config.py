from decimal import Decimal
from dash import constants

# NOTE: keep in sync with R1 (https://github.com/Zemanta/r1/blob/bcad62e93fdbd587395cfdfa2338b889374e1d84/config/config.go#L69)
AUTOMATION_CAMPAIGN = 830
AUTOMATION_USER_EMAIL = 'businesswire-user@zemanta.com'

TEST_FEED_AD_GROUP = 2780

AD_GROUP_NAME_TEMPLATE = '{start_date} - {interest_targeting_str}'
DEFAULT_CPC = Decimal('0.2')
DEFAULT_DAILY_BUDGET = 800

INTEREST_TARGETING_OPTIONS = [
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

INTEREST_TARGETING_GROUPS = [  # every category in here also has to be in INTEREST_TARGETING_OPTIONS
]

NOTIFICATION_EMAILS = [
    'luka.silovinac@zemanta.com',
    # 'bostjan@zemanta.com',
]
