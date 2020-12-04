import rest_framework.fields
import rest_framework.serializers

import dash.constants
import dash.features.contentupload
import dash.models
import restapi.serializers.base
import restapi.serializers.fields
import restapi.serializers.serializers


class ApprovalStatusSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    slug = rest_framework.serializers.CharField(source="bidder_slug", required=True)
    status = restapi.serializers.fields.DashConstantField(
        dash.constants.ContentAdSubmissionStatus, required=True, source="submission_status"
    )
    reason = rest_framework.serializers.CharField(required=True, allow_null=True, source="submission_errors")


class TrackerSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    event_type = restapi.serializers.fields.DashConstantField(dash.constants.TrackerEventType, required=True)
    method = restapi.serializers.fields.DashConstantField(dash.constants.TrackerMethod, required=True)
    url = restapi.serializers.fields.HttpsURLField(
        required=True,
        error_messages={"invalid": "Invalid tracker URL", "invalid_schema": "Tracker URL has to be HTTPS"},
    )
    fallback_url = restapi.serializers.fields.HttpsURLField(
        required=False,
        default=None,
        error_messages={
            "invalid": "Invalid fallback tracker URL",
            "invalid_schema": "Fallback tracker URL has to be HTTPS",
        },
    )
    tracker_optional = rest_framework.fields.BooleanField(required=False, default=False)

    def validate(self, data):
        data = super().validate(data)
        if (
            data.get("event_type") != dash.constants.TrackerEventType.IMPRESSION
            and data.get("method") == dash.constants.TrackerMethod.JS
        ):
            raise rest_framework.serializers.ValidationError(
                {"method": "Javascript Tag method cannot be used together with Viewability type."}
            )
        return data

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        value["supported_privacy_frameworks"] = dash.features.contentupload.get_privacy_frameworks(
            data.get("url"), data.get("fallback_url")
        )
        return value


class TrackersSerializer(rest_framework.serializers.ListSerializer):
    def __init__(self, *args, **kwargs):
        self.child = TrackerSerializer()
        super().__init__(*args, **kwargs)

    def validate(self, trackers):
        if len(trackers) > 3:
            raise rest_framework.serializers.ValidationError("A maximum of three trackers is supported.")
        return trackers


class ContentAdSerializer(
    restapi.serializers.serializers.PermissionedFieldsMixin, rest_framework.serializers.ModelSerializer
):
    class Meta:
        model = dash.models.ContentAd
        fields = (
            "id",
            "ad_group_id",
            "state",
            "type",
            "url",
            "title",
            "image_url",
            "icon_url",
            "display_url",
            "brand_name",
            "description",
            "call_to_action",
            "label",
            "image_crop",
            "tracker_urls",
            "additional_data",
            "ad_width",
            "ad_height",
            "ad_tag",
            "video_asset_id",
            "approval_status",
            "trackers",
        )
        read_only_fields = tuple(
            set(fields) - set(("state", "url", "tracker_urls", "trackers", "label", "additional_data", "brand_name"))
        )
        permissioned_fields = {
            "additional_data": "zemauth.can_use_ad_additional_data",
            "type": "zemauth.fea_can_change_campaign_type_to_display",
            "ad_width": "zemauth.fea_can_change_campaign_type_to_display",
            "ad_height": "zemauth.fea_can_change_campaign_type_to_display",
            "ad_tag": "zemauth.fea_can_change_campaign_type_to_display",
            "trackers": "zemauth.can_use_3rdparty_js_trackers",
        }

    def to_representation(self, ad):
        ret = super().to_representation(ad)

        if ad.ad_group.campaign.type != dash.constants.CampaignType.DISPLAY:
            ret.pop("type", None)
            ret.pop("ad_width", None)
            ret.pop("ad_height", None)
            ret.pop("ad_tag", None)

        if ad.ad_group.campaign.type != dash.constants.CampaignType.VIDEO:
            ret.pop("video_asset_id", None)

        return ret

    id = restapi.serializers.fields.IdField(required=False)
    ad_group_id = restapi.serializers.fields.IdField(source="ad_group", required=False)
    state = restapi.serializers.fields.DashConstantField(dash.constants.ContentAdSourceState, required=False)
    url = rest_framework.serializers.URLField(required=False)
    image_url = rest_framework.serializers.URLField(source="get_image_url", required=False)
    icon_url = rest_framework.serializers.URLField(source="get_icon_url", required=False)
    type = restapi.serializers.fields.DashConstantField(
        dash.constants.AdType, default=dash.constants.AdType.CONTENT, required=False
    )
    ad_width = rest_framework.serializers.IntegerField(source="image_width", required=False)
    ad_height = rest_framework.serializers.IntegerField(source="image_height", required=False)
    ad_tag = rest_framework.serializers.CharField(required=False)
    video_asset_id = rest_framework.serializers.UUIDField(source="video_asset.id", required=False)
    approval_status = ApprovalStatusSerializer(read_only=True, many=True, required=False)
    trackers = TrackersSerializer(allow_null=True, required=False)


class ContentAdCandidateSerializer(
    restapi.serializers.serializers.PermissionedFieldsMixin, rest_framework.serializers.ModelSerializer
):
    class Meta:
        model = dash.models.ContentAdCandidate
        fields = (
            "url",
            "title",
            "image_url",
            "icon_url",
            "display_url",
            "brand_name",
            "description",
            "call_to_action",
            "state",
            "label",
            "image_crop",
            "additional_data",
            "video_asset_id",
            "trackers",
        )
        extra_kwargs = {"primary_tracker_url": {"allow_empty": True}, "secondary_tracker_url": {"allow_empty": True}}
        permissioned_fields = {
            "additional_data": "zemauth.can_use_ad_additional_data",
            "trackers": "zemauth.can_use_3rdparty_js_trackers",
        }

    url = restapi.serializers.fields.PlainCharField(required=True)
    title = restapi.serializers.fields.PlainCharField(required=True)
    image_url = restapi.serializers.fields.PlainCharField(required=True)
    icon_url = restapi.serializers.fields.PlainCharField(required=False)
    display_url = restapi.serializers.fields.PlainCharField(required=True)
    brand_name = restapi.serializers.fields.PlainCharField(required=True)
    description = restapi.serializers.fields.PlainCharField(required=True)
    call_to_action = restapi.serializers.fields.PlainCharField(required=True)
    image_crop = restapi.serializers.fields.PlainCharField(required=True)
    label = restapi.serializers.fields.PlainCharField(allow_blank=True, allow_null=True, required=False)
    video_asset_id = rest_framework.serializers.UUIDField(required=False)
    state = restapi.serializers.fields.DashConstantField(dash.constants.ContentAdSourceState, required=False)
    trackers = TrackersSerializer(allow_null=True, required=False)

    def to_internal_value(self, external_data):
        internal_data = super(ContentAdCandidateSerializer, self).to_internal_value(external_data)
        tracker_urls = external_data.get("tracker_urls")
        if not tracker_urls:
            return internal_data
        if len(tracker_urls) > 0:
            internal_data["primary_tracker_url"] = tracker_urls[0]
        if len(tracker_urls) > 1:
            internal_data["secondary_tracker_url"] = tracker_urls[1]
        if len(tracker_urls) > 2:
            raise rest_framework.serializers.ValidationError("A maximum of two tracker URLs are supported.")
        return internal_data


class ImageAdCandidateSerializer(ContentAdCandidateSerializer):
    class Meta:
        model = dash.models.ContentAdCandidate
        fields = ("url", "title", "image_url", "display_url", "label", "type", "trackers")
        permissioned_fields = {
            "additional_data": "zemauth.can_use_ad_additional_data",
            "type": "zemauth.fea_can_change_campaign_type_to_display",
            "trackers": "zemauth.can_use_3rdparty_js_trackers",
        }

    type = restapi.serializers.fields.DashConstantField(dash.constants.AdType)
    url = restapi.serializers.fields.PlainCharField(required=True)
    title = restapi.serializers.fields.PlainCharField(required=True)
    image_url = restapi.serializers.fields.PlainCharField(required=True)
    display_url = restapi.serializers.fields.PlainCharField(required=True)
    label = restapi.serializers.fields.PlainCharField(allow_blank=True, allow_null=True, required=False)
    trackers = TrackersSerializer(allow_null=True, required=False)


class AdTagCandidateSerializer(ContentAdCandidateSerializer):
    class Meta:
        model = dash.models.ContentAdCandidate
        fields = ("url", "title", "display_url", "label", "type", "ad_tag", "ad_width", "ad_height", "trackers")
        extra_kwargs = {"primary_tracker_url": {"allow_empty": True}, "secondary_tracker_url": {"allow_empty": True}}
        permissioned_fields = {
            "additional_data": "zemauth.can_use_ad_additional_data",
            "type": "zemauth.fea_can_change_campaign_type_to_display",
            "ad_width": "zemauth.fea_can_change_campaign_type_to_display",
            "ad_height": "zemauth.fea_can_change_campaign_type_to_display",
            "ad_tag": "zemauth.fea_can_change_campaign_type_to_display",
            "trackers": "zemauth.can_use_3rdparty_js_trackers",
        }

    type = restapi.serializers.fields.DashConstantField(dash.constants.AdType)
    url = restapi.serializers.fields.PlainCharField(required=True)
    title = restapi.serializers.fields.PlainCharField(required=True)
    display_url = restapi.serializers.fields.PlainCharField(required=True)
    label = restapi.serializers.fields.PlainCharField(allow_blank=True, allow_null=True, required=False)
    ad_tag = rest_framework.serializers.CharField(required=True)
    ad_width = rest_framework.serializers.IntegerField(source="image_width", required=True)
    ad_height = rest_framework.serializers.IntegerField(source="image_height", required=True)
    trackers = TrackersSerializer(allow_null=True, required=False)


class AdTypeSerializer(rest_framework.serializers.Serializer):
    type = restapi.serializers.fields.DashConstantField(
        dash.constants.AdType, default=dash.constants.AdType.CONTENT, required=False
    )


class UploadBatchSerializer(rest_framework.serializers.Serializer):
    id = restapi.serializers.fields.IdField()
    status = restapi.serializers.fields.DashConstantField(dash.constants.UploadBatchStatus)
    approvedContentAds = ContentAdSerializer(many=True, source="get_approved_content_ads")

    def to_representation(self, batch):
        external_data = super(UploadBatchSerializer, self).to_representation(batch)
        cleaned_candidates = dash.features.contentupload.upload.get_candidates_with_errors(
            None, batch.contentadcandidate_set.all()
        )
        external_data["validationStatus"] = [candidate["errors"] for candidate in cleaned_candidates]
        return external_data


class ContentAdQueryParams(
    restapi.serializers.serializers.QueryParamsExpectations, restapi.serializers.serializers.PaginationParametersMixin
):
    include_approval_status = rest_framework.serializers.BooleanField(default=False)


class ContentAdListQueryParams(
    ContentAdQueryParams,
    restapi.serializers.serializers.QueryParamsExpectations,
    restapi.serializers.serializers.PaginationParametersMixin,
):
    ad_group_id = restapi.serializers.fields.IdField(required=True)
