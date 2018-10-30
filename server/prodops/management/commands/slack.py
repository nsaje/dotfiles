import sys

import utils.command_helpers
import utils.slack


class Command(utils.command_helpers.ExceptionCommand):
    help = "Post on slack"

    def add_arguments(self, parser):
        parser.add_argument("msg", nargs="?", help="Message")
        parser.add_argument("--error", dest="is_error", action="store_true", help="Error")
        parser.add_argument("--warn", dest="is_warning", action="store_true", help="Warning")
        parser.add_argument("--success", dest="is_success", action="store_true", help="Success")

    def handle(self, *args, **options):
        msg_type = utils.slack.MESSAGE_TYPE_INFO
        if options.get("is_error"):
            msg_type = utils.slack.MESSAGE_TYPE_CRITICAL
        elif options.get("is_warning"):
            msg_type = utils.slack.MESSAGE_TYPE_WARNING
        elif options.get("is_success"):
            msg_type = utils.slack.MESSAGE_TYPE_SUCCESS
        utils.slack.publish(options.get("msg") or sys.stdin.read(), msg_type=msg_type, username="Slack command")
