from django.db import transaction

import dash.constants
import utils.email_helper
import utils.exc
import utils.k1_helper
import utils.redirector_helper
from utils import zlogging

logger = zlogging.getLogger(__name__)

VALID_UPDATE_FIELDS = set(
    [
        "type",
        "url",
        "brand_name",
        "display_url",
        "description",
        "image_crop",
        "label",
        "tracker_urls",
        "trackers",
        "call_to_action",
        "additional_data",
        "ad_tag",
        "image_width",
        "image_height",
        "icon",
        "document_id",
        "document_features",
        "state",
        "url",
        "archived",
    ]
)


class ContentAdInstanceMixin(object):
    @transaction.atomic()
    def update(self, request, write_history=True, **updates):
        changes = self._clean_updates(updates)
        if not changes:
            return

        self._validate_update(changes)
        self._apply_changes_and_save(request, changes)

        if "url" in changes:
            self._update_url(request)
        if "state" in changes:
            self._update_content_ad_sources_state(request)

        if write_history:
            self._write_change_history(request, changes)

        utils.k1_helper.update_content_ad(self, msg="ContentAd.update")

    def _clean_updates(self, updates):
        new_updates = {}

        for field, value in list(updates.items()):
            if field in VALID_UPDATE_FIELDS and value != getattr(self, field):
                new_updates[field] = value

        return new_updates

    def _validate_update(self, changes):
        if self.archived or self.ad_group.is_archived():
            raise utils.exc.EntityArchivedError(
                "Account, campaign, ad group and content ad must not be archived in order to update a content ad."
            )

    def _apply_changes_and_save(self, request, changes):
        for field, value in list(changes.items()):
            if field in VALID_UPDATE_FIELDS:
                setattr(self, field, value)
        self.save()

    def save(self, *args, **kwargs):
        try:
            self._handle_oen_document_data()
        except Exception:
            logger.exception("Something went wrong when trying to map OEN's document data")
        super().save(*args, **kwargs)

    def _handle_oen_document_data(self):
        if not self.additional_data:
            return

        oen_document_id = self.additional_data.get("document_id")
        if oen_document_id and oen_document_id != self.document_id:
            self.document_id = oen_document_id

        document_features_updates = {}
        if "language" in self.additional_data:
            document_features_updates["language"] = [
                {"value": self.additional_data["language"].lower(), "confidence": 1.0}
            ]
        if "document_features" in self.additional_data:
            document_features_updates["categories"] = self.additional_data["document_features"]
        if "iab_categories_v1" in self.additional_data:
            document_features_updates["iab_categories_v1"] = self.additional_data["iab_categories_v1"]
        if "domain" in self.additional_data:
            document_features_updates["domain"] = self.additional_data["domain"]

        if document_features_updates:
            if not self.document_features:
                self.document_features = {}
            self.document_features.update(document_features_updates)

    def _write_change_history(self, request, changes):
        description = "Content ad {id} edited.".format(id=self.pk)
        self.ad_group.write_history(
            description,
            user=request and request.user or None,
            action_type=dash.constants.HistoryActionType.CONTENT_AD_EDIT,
        )

    @transaction.atomic()
    def _update_content_ad_sources_state(self, request):
        self.contentadsource_set.all().update(state=self.state)
        description = "Content ad {id} set to {state}.".format(
            id=self.pk, state=dash.constants.ContentAdSourceState.get_text(self.state)
        )
        self.ad_group.write_history(
            description,
            user=request and request.user or None,
            action_type=dash.constants.HistoryActionType.CONTENT_AD_STATE_CHANGE,
        )
        utils.k1_helper.update_content_ad(self, msg="ContentAd.set_state")
        if request:
            utils.email_helper.send_ad_group_notification_email(self.ad_group, request, description)

    @transaction.atomic()
    def _update_url(self, request):
        description = "Content ad {id} url set to {url}.".format(id=self.pk, url=self.url)
        self.ad_group.write_history(
            description,
            user=request and request.user or None,
            action_type=dash.constants.HistoryActionType.CONTENT_AD_EDIT,
        )
        utils.redirector_helper.update_redirect(self.url, self.redirect_id)
