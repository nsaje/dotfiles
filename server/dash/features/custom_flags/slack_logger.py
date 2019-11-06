from utils import slack
from utils import zlogging

from .model import CustomFlag

logger = zlogging.getLogger(__name__)


class SlackLoggerMixin(object):
    def log_custom_flags_event_to_slack(self, original_entity, updated_entity, user=None):
        all_flags_default = {cf.id: cf.get_default_value() for cf in CustomFlag.objects.all()}
        orignal_flags = original_entity.custom_flags or all_flags_default
        updated_flags = updated_entity.custom_flags or all_flags_default

        messages = []
        for cf_id, cf_value in updated_flags.items():
            if cf_id in orignal_flags.keys() and orignal_flags[cf_id] != cf_value:
                messages.append(
                    "Custom flag *{cf}* value has been changed from *{old_value}* to *{new_value}* on {entity_link}"
                    " ({type}). -- {modified_by}".format(
                        cf=cf_id,
                        old_value=orignal_flags[cf_id],
                        new_value=cf_value,
                        entity_link=self.entity_admin_url_builder(updated_entity, anchor_tag=updated_entity.name),
                        type=original_entity.__class__.__name__,
                        modified_by="Modified by: {}".format(user) if user else "",
                    )
                )
        text = "\n".join(messages)

        if text.strip():
            try:
                slack.publish(text, channel=slack.CHANNEL_ZEM_FEED_HACKS)
            except Exception:
                logger.exception("Connection Error with Slack")

    def entity_admin_url_builder(self, entity, domain="https://one.zemanta.com", anchor_tag="edit"):
        entity_name = entity.__class__.__name__.lower()
        url = "{domain}/admin/dash/{entity_name}/{id}/change/".format(
            domain=domain, entity_name=entity_name, id=entity.id
        )
        return slack.link(url, anchor_tag)
