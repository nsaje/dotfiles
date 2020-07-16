import dash.constants

SALESFORCE_SERVICE_NAME = "salesforce"
DEFAULT_ACCOUNT_TYPE = dash.constants.AccountType.PILOT
CLIENT_TYPE_AGENCY = "agency"
CLIENT_TYPE_CLIENT_DIRECT = "brand"
# TODO (tfischer): handle properly via SF
DEFAULT_CS_REPRESENTATIVE = "christian.marchan@zemanta.com"
DEFAULT_SALES_REPRESENTATIVE = "david.kaplan@zemanta.com"
ACCOUNT_ID_PREFIX_AGENCY = "a"
ACCOUNT_ID_PREFIX_CLIENT_DIRECT = "b"
PF_SCHEDULE_UPFRONT = "upon execution of this agreement"  # flat
PF_SCHEDULE_PCT_FEE = "monthly as used"  # %
PF_SCHEDULE_FLAT_FEE = "monthly in installments"

ENTITY_TAGS_PREFIX = "dmr/"
ENTITY_TAGS_US = "NA-US"
ENTITY_TAGS_INTL = "Intl"
