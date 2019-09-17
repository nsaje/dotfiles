import logging

from django.db import transaction

import dash.constants
import utils.email_helper
import utils.exc
import utils.k1_helper
import utils.redirector_helper

logger = logging.getLogger(__name__)

OEN_ACCOUNT_ID = 305

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
        "call_to_action",
        "additional_data",
        "ad_tag",
        "image_width",
        "image_height",
        "icon_size",
        "document_id",
        "document_features",
    ]
)


class ContentAdInstanceMixin(object):
    @transaction.atomic()
    def set_state(self, request, state):
        self.state = state
        self.save()
        self.contentadsource_set.all().update(state=state)

        description = "Content ad {id} set to {state}.".format(
            id=self.pk, state=dash.constants.ContentAdSourceState.get_text(state)
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
    def set_url(self, request, url):
        self.url = url
        self.save()

        description = "Content ad {id} url set to {url}.".format(id=self.pk, url=url)
        self.ad_group.write_history(
            description,
            user=request and request.user or None,
            action_type=dash.constants.HistoryActionType.CONTENT_AD_EDIT,
        )
        utils.redirector_helper.update_redirect(url, self.redirect_id)

    @transaction.atomic()
    def update(self, request, write_history=True, **updates):
        changes = self._clean_updates(updates)
        if not changes:
            return

        self._validate_update(changes)
        self._apply_changes_and_save(request, changes)

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
            raise utils.exc.ForbiddenError(
                "Account, campaign, ad group and content ad must not be archived in order to update a content ad."
            )

    def _apply_changes_and_save(self, request, changes):
        for field, value in list(changes.items()):
            if field in VALID_UPDATE_FIELDS:
                setattr(self, field, value)
        try:
            self._handle_oen_document_data()
        except Exception:
            logger.exception("Something went wrong when trying to map OEN's document data")
        self.save()

    def _handle_oen_document_data(self):
        if not self.ad_group.campaign.account_id == OEN_ACCOUNT_ID or not self.additional_data:
            return

        oen_document_id = self.additional_data.get("document_id")
        if oen_document_id and oen_document_id != self.document_id:
            self.document_id = oen_document_id
            self.document_features = self._remap_document_feature_fields(self.additional_data)

    def _write_change_history(self, request, changes):
        description = "Content ad {id} edited.".format(id=self.pk)
        self.ad_group.write_history(
            description,
            user=request and request.user or None,
            action_type=dash.constants.HistoryActionType.CONTENT_AD_EDIT,
        )

    @staticmethod
    def _remap_document_feature_fields(additional_data):
        document_features = {}
        if "language" in additional_data:
            document_features["language"] = [{"value": additional_data["language"].lower(), "confidence": 1.0}]
        if "document_features" in additional_data:
            document_features["categories"] = additional_data["document_features"]
        return document_features
