import logging

from utils import slack

logger = logging.getLogger(__name__)

ACCOUNT_URL = "https://one.zemanta.com/v2/credit/account/{}"
CAMPAIGN_URL = "https://one.zemanta.com/v2/analytics/campaign/{}?settings"

SLACK_SKIP_LOG_ACCOUNTS = (305, )
SLACK_NEW_CREDIT_MSG = u"New credit #{credit_id} added on account <{url}|{account_name}> with amount ${amount} and end date {end_date}."
SLACK_UPDATED_CREDIT_MSG = u"Credit #{credit_id} on account <{url}|{account_name}> updated: {history}"
SLACK_NEW_BUDGET_MSG = u"New budget #{budget_id} added on campaign <{url}|{campaign_name}> with amount ${amount} and end date {end_date}."
SLACK_UPDATED_BUDGET_MSG = u"Budget #{budget_id} on campaign <{url}|{campaign_name}> updated: {history}"


def log_to_slack(account_id, msg):
    if account_id in SLACK_SKIP_LOG_ACCOUNTS:
        return
    try:
        slack.publish(
            msg,
            channel='bcm',
            username='z1'
        )
    except:
        logger.exception('Failed to publish to slack')
