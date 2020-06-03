from django.conf import settings

from utils import slack
from utils import zlogging

logger = zlogging.getLogger(__name__)

AGENCY_URL = "https://one.zemanta.com/v2/credits?agencyId={agency_id}"
ACCOUNT_URL = "https://one.zemanta.com/v2/credits?agencyId={agency_id}&accountId={account_id}"
CAMPAIGN_URL = "https://one.zemanta.com/v2/analytics/campaign/{campaign_id}(drawer:settings)?settingsEntityType=campaign&settingsEntityId={campaign_id}"

SLACK_SKIP_LOG_ACCOUNTS = (settings.HARDCODED_ACCOUNT_ID_OEN,)

SLACK_NEW_CREDIT_MSG = "New credit #{credit_id} added on account <{url}|{account_name}> with amount {currency_symbol}{amount} and end date {end_date}."
SLACK_NEW_CREDIT_WITHOUT_CONTRACT_MSG = "New credit #{credit_id} added on account <{url}|{account_name}> with amount {currency_symbol}{amount} and end date {end_date} *has been created without contract ID or contract Number!* {comment}"

SLACK_NEW_AGENCY_CREDIT_MSG = "New agency credit #{credit_id} added to agency <{url}|{agency_name}> with amount {currency_symbol}{amount} and end date {end_date}."
SLACK_NEW_AGENCY_CREDIT_WITHOUT_CONTRACT_MSG = "New credit #{credit_id} added to agency <{url}|{agency_name}> with amount {currency_symbol}{amount} and end date {end_date} *has been created without contract ID or contract Number!* {comment}"

SLACK_UPDATED_CREDIT_MSG = "Credit #{credit_id} on account <{url}|{account_name}> updated: {history}"
SLACK_UPDATED_AGENCY_CREDIT_MSG = "Credit #{credit_id} on agency <{url}|{agency_name}> updated: {history}"

SLACK_NEW_BUDGET_MSG = "New budget #{budget_id} added on campaign <{url}|{campaign_name}> with amount {currency_symbol}{amount} (including {margin}% of margin) and end date {end_date}."
SLACK_UPDATED_BUDGET_MSG = "Budget #{budget_id} on campaign <{url}|{campaign_name}> updated: {history}"


def log_to_slack(account_id, msg, msg_type=slack.MESSAGE_TYPE_INFO):
    if account_id in SLACK_SKIP_LOG_ACCOUNTS:
        return
    try:
        slack.publish(msg, channel=slack.CHANNEL_ZEM_FEED_BUDGETS, username=slack.USER_BCM, msg_type=msg_type)
    except Exception:
        logger.exception("Failed to publish to slack")
