import dash.constants

ACCOUNT_ID_PREFIX_AGENCY = "a"
ACCOUNT_ID_PREFIX_CLIENT_DIRECT = "b"

CLIENT_TYPE_AGENCY = "agency"
CLIENT_TYPE_CLIENT_DIRECT = "brand"

PF_SCHEDULE_UPFRONT = "upon execution of this agreement"  # flat
PF_SCHEDULE_PCT_FEE = "monthly as used"  # %
PF_SCHEDULE_FLAT_FEE = "monthly in installments"

OUTBRAIN_CURRENCIES = [
    dash.constants.Currency.USD,
    dash.constants.Currency.EUR,
    dash.constants.Currency.GBP,
    dash.constants.Currency.AUD,
    dash.constants.Currency.SGD,
    dash.constants.Currency.BRL,
    dash.constants.Currency.MYR,
    dash.constants.Currency.CHF,
]
