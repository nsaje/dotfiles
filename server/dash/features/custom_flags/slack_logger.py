from utils import slack
import logging


logger = logging.getLogger(__name__)


class SlackLoggerMixin(object):
    def log_custom_flags_event_to_slack(self, original_entity, updated_entity):

        orignal_flags = original_entity.custom_flags or dict()
        updated_flags = updated_entity.custom_flags or dict()
        removed = set(orignal_flags.keys()) - set(updated_flags.keys())
        added = set(updated_flags.keys()) - set(orignal_flags.keys())
        entity_type = original_entity.__class__.__name__
        removed_msg = ""
        added_msg = ""

        if removed:
            removed_msg = "*{ids}* have been disabled on {entity_link} ({type}).".format(
                ids=", ".join(removed),
                entity_link=self.entity_admin_url_builder(original_entity, anchor_tag=original_entity.name),
                type=entity_type,
            )
        if added:
            added_msg = "*{ids}* have been enabled on {entity_link} ({type}).".format(
                ids=", ".join(added),
                entity_link=self.entity_admin_url_builder(original_entity, anchor_tag=updated_entity.name),
                type=entity_type,
            )

        txt = "\n".join([removed_msg, added_msg])
        if txt.strip():
            try:
                slack.publish(txt, channel="z1-hacks-logs")
            except Exception:
                logger.exception("Connection Error with Slack")

    def entity_admin_url_builder(self, entity, domain="https://one.zemanta.com", anchor_tag="edit"):
        entity_name = entity.__class__.__name__.lower()
        url = "{domain}/admin/dash/{entity_name}/{id}/change".format(
            domain=domain, entity_name=entity_name, id=entity.id
        )
        return slack.link(url, anchor_tag)
