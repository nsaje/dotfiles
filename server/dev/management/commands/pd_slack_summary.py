import datetime
from collections import defaultdict

from utils import dates_helper
from utils import pagerduty_helper
from utils import slack
from utils import zlogging
from utils.command_helpers import Z1Command

logger = zlogging.getLogger(__name__)


# only contains names that need to be overriden, most match with email
EMAIL_TO_SLACK_OVERRIDE = {}
SLACK_USER = "PagerDuty Assistant"
LONG_INCIDENT_HOURS = 12


class Command(Z1Command):

    help = "Posts active PagerDuty incidents to Slack"

    def handle(self, *args, **options):
        user_on_call = pagerduty_helper.get_on_call_user()
        active_incidents = pagerduty_helper.list_active_incidents()
        if user_on_call:
            self.notify_user_on_call(user_on_call)
        if active_incidents:
            self.list_active_incidents(active_incidents)
            self.notify_individuals_of_long_incidents(active_incidents)
        else:
            slack.publish(
                "No active incidents right now. Woohoo!",
                channel=slack.CHANNEL_RND_Z1_ALERTS,
                msg_type=slack.MESSAGE_TYPE_SUCCESS,
                username=SLACK_USER,
            )

    @classmethod
    def notify_user_on_call(cls, user_on_call):
        slack_handle = cls._get_slack_handle(user_on_call)
        slack.publish(
            f"Good morning @{slack_handle}! You're on call today!",
            channel=slack.CHANNEL_RND_Z1_ALERTS,
            msg_type=slack.MESSAGE_TYPE_INFO,
            username=SLACK_USER,
            link_names=True,
        )

    @staticmethod
    def list_active_incidents(active_incidents):
        msg_type = slack.MESSAGE_TYPE_WARNING if len(active_incidents) < 3 else slack.MESSAGE_TYPE_CRITICAL
        message = "The following incidents are active and need your attention:"
        for incident in active_incidents:
            message += "\n - " + slack.link(incident.url, incident.title)
        slack.publish(message, channel=slack.CHANNEL_RND_Z1_ALERTS, msg_type=msg_type, username=SLACK_USER)

    @classmethod
    def notify_individuals_of_long_incidents(cls, active_incidents):
        per_user = defaultdict(list)
        for incident in active_incidents:
            if incident.created_at > dates_helper.utc_now() - datetime.timedelta(hours=LONG_INCIDENT_HOURS):
                continue
            user = pagerduty_helper.get_user(incident.assignee_id)
            per_user[user].append(incident)

        for user, incidents in per_user.items():
            first_name = user.name.split(" ")[0]
            message = f"Hey {first_name}! The following incidents have been active for more than {LONG_INCIDENT_HOURS} hours and would ideally be looked at today:"
            for incident in incidents:
                message += "\n - " + slack.link(incident.url, incident.title)
            channel = "@" + cls._get_slack_handle(user)
            slack.publish(message, channel=channel, msg_type=slack.MESSAGE_TYPE_WARNING, username=SLACK_USER)

    @staticmethod
    def _get_slack_handle(user):
        email_name = user.email.split("@")[0]
        return EMAIL_TO_SLACK_OVERRIDE.get(email_name, email_name)
