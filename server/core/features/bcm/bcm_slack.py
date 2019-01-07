import logging

from utils import slack

logger = logging.getLogger(__name__)

ACCOUNT_URL = "https://one.zemanta.com/v2/credit/account/{}"
CAMPAIGN_URL = "https://one.zemanta.com/v2/analytics/campaign/{}?settings"

SLACK_CHANNEL = "z1-budget-feed"
SLACK_SKIP_LOG_ACCOUNTS = (305,)
SLACK_NEW_CREDIT_MSG = "New credit #{credit_id} added on account <{url}|{account_name}> with amount {currency_symbol}{amount} and end date {end_date}."
SLACK_NEW_CREDIT_WITHOUT_CONTRACT_MSG = "New credit #{credit_id} added on account <{url}|{account_name}> with amount {currency_symbol}{amount} and end date {end_date} *has been created without contract ID or contract Number!* {comment}"
SLACK_NEW_AGENCY_CREDIT_MSG = "New agency credit #{credit_id} added to agency {agency} with amount {currency_symbol}{amount} and end date {end_date}."
SLACK_UPDATED_CREDIT_MSG = "Credit #{credit_id} on account <{url}|{account_name}> updated: {history}"
SLACK_NEW_BUDGET_MSG = "New budget #{budget_id} added on campaign <{url}|{campaign_name}> with amount {currency_symbol}{amount} (including {margin}% of margin) and end date {end_date}."
SLACK_UPDATED_BUDGET_MSG = "Budget #{budget_id} on campaign <{url}|{campaign_name}> updated: {history}"


def log_to_slack(account_id, msg, msg_type=slack.MESSAGE_TYPE_INFO):
    if account_id in SLACK_SKIP_LOG_ACCOUNTS:
        return
    try:
        slack.publish(msg, channel=SLACK_CHANNEL, username="z1", msg_type=msg_type)
    except Exception:
        logger.exception("Failed to publish to slack")
