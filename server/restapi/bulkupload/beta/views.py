
import core.features.bulk_upload
import zemauth.access
from restapi.common.views_base import RESTAPIBaseViewSet
from zemauth.features.entity_permission import Permission

from . import serializers


class BulkAdGroupsViewSet(RESTAPIBaseViewSet):
    def get(self, request, task_id):
        promise = core.features.bulk_upload.get_upload_promise(task_id)
        return self._handle_promise(promise)

    def create(self, request):
        serializer = serializers.AdGroupCustomSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        for ad_group in data:
            zemauth.access.get_campaign(request.user, Permission.WRITE, ad_group.get("ad_group", {}).get("campaign_id"))

        promise = core.features.bulk_upload.upload_adgroups.delay(request.user, data)
        return self._handle_promise(promise)

    def _handle_promise(self, promise):
        status = promise.status
        ad_groups_settings = None
        if promise.successful():
            ad_groups_settings = []
            ad_groups, batches = promise.result
            for ad_group, batch in zip(ad_groups, batches):
                ad_group.settings.ads = batch.contentad_set.all()
                ad_group.settings.sources = ad_group.sources.filter(adgroupsource__settings__state=1)
                ad_groups_settings.append(ad_group.settings)
        return self.response_ok(
            serializers.TaskStatus({"task_id": promise.id, "status": status, "ad_groups": ad_groups_settings}).data
        )
