from utils import pagerduty_helper
from utils import slack
from utils import zlogging
from utils.command_helpers import Z1Command

logger = zlogging.getLogger(__name__)


# only contains names that need to be overriden, most match with email
EMAIL_TO_SLACK_OVERRIDE = {"lsilovinac": "luka"}
SLACK_USER = "PagerDuty Assistant"


class Command(Z1Command):

    help = "Posts active PagerDuty incidents to Slack"

    def handle(self, *args, **options):
        user_on_call = pagerduty_helper.get_on_call_user()
        active_incidents = pagerduty_helper.list_active_incidents()
        if user_on_call:
            email_name = user_on_call.email.split("@")[0]
            slack_handle = EMAIL_TO_SLACK_OVERRIDE.get(email_name, email_name)
            slack.publish(
                f"Good morning @{slack_handle}! You're on call today!",
                channel=slack.CHANNEL_RND_Z1_ALERTS,
                msg_type=slack.MESSAGE_TYPE_INFO,
                username=SLACK_USER,
                link_names=True,
            )
        if active_incidents:
            msg_type = slack.MESSAGE_TYPE_WARNING if len(active_incidents) < 3 else slack.MESSAGE_TYPE_CRITICAL
            message = "The following incidents are active and need your attention:"
            for incident in active_incidents:
                message += "\n - " + slack.link(incident.url, incident.title)
            slack.publish(message, channel=slack.CHANNEL_RND_Z1_ALERTS, msg_type=msg_type, username=SLACK_USER)
        else:
            slack.publish(
                "No active incidents right now. Woohoo!",
                channel=slack.CHANNEL_RND_Z1_ALERTS,
                msg_type=slack.MESSAGE_TYPE_SUCCESS,
                username=SLACK_USER,
            )
