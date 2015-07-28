from threading import Thread
import logging

import actionlog.zwei_actions

logger = logging.getLogger(__name__)


class SendActionLogsThread(Thread):
    def __init__(self, action_logs, *args, **kwargs):
        self.action_logs = action_logs
        super(SendActionLogsThread, self).__init__(*args, **kwargs)

    def run(self):
        actionlog.zwei_actions.send_multiple(self.action_logs)
