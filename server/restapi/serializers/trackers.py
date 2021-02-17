import rest_framework.fields
import rest_framework.serializers

import dash.constants
import dash.features.contentupload
import dash.models
import restapi.serializers.base
import restapi.serializers.fields
import restapi.serializers.serializers


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
    tracker_optional = rest_framework.fields.BooleanField(required=False, default=True)

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
        tracker_limit = dash.features.contentupload.MAX_TRACKERS
        request = self.context.get("request")
        if request and request.user.has_perm("zemauth.can_use_extra_trackers"):
            tracker_limit = dash.features.contentupload.MAX_TRACKERS_EXTRA

        if len(trackers) > tracker_limit:
            raise rest_framework.serializers.ValidationError(
                "A maximum of {} trackers is supported.".format(tracker_limit)
            )
        return trackers
