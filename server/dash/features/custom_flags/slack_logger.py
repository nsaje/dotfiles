from utils import slack
import logging


logger = logging.getLogger(__name__)


class SlackLoggerMixin(object):
    def log_custom_flags_event_to_slack(self, original_entity, updated_entity):
        try:
            removed = set(original_entity.custom_flags.keys()) - set(updated_entity.custom_flags.keys())
            added = set(updated_entity.custom_flags.keys()) - set(original_entity.custom_flags.keys())
            removed_msg = ''
            added_msg = ''

            if removed:
                removed_msg = '{ids} have been disabled on {entity}.'.format(ids=', '.join(removed),
                                                                             entity=original_entity.name)
            if added:
                added_msg = '{ids} have been enabled on {entity}.'.format(ids=', '.join(added),
                                                                          entity=original_entity.name)

            txt = '\n'.join([removed_msg, added_msg])
            slack.publish(txt, channel='z1-hacks-logs')

        except Exception:
            logger.exception('Connection Error with Slack')
