from restapi.common.views_base import RESTAPIBaseViewSet
import restapi.access

from core.entity.settings.ad_group_settings import exceptions
from . import serializers
import utils.exc


class AdGroupSourcesRTBViewSet(RESTAPIBaseViewSet):

    def get(self, request, ad_group_id):
        ad_group = restapi.access.get_ad_group(request.user, ad_group_id)
        return self.response_ok(
            serializers.AdGroupSourcesRTBSerializer(ad_group.settings).data
        )

    def put(self, request, ad_group_id):
        ad_group = restapi.access.get_ad_group(request.user, ad_group_id)
        serializer = serializers.AdGroupSourcesRTBSerializer(
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        self.update_settings(request, ad_group, serializer.validated_data)
        return self.response_ok(
            serializers.AdGroupSourcesRTBSerializer(ad_group.settings).data
        )

    def update_settings(self, request, ad_group, settings):
        try:
            ad_group.settings.update(request, **settings)

        except exceptions.AdGroupNotPaused as err:
            raise utils.exc.ValidationError(errors={'group_enabled': [str(err)]})

        except exceptions.DailyBudgetAutopilotNotDisabled as err:
            raise utils.exc.ValidationError(errors={'daily_budget': [str(err)]})

        except exceptions.CPCAutopilotNotDisabled as err:
            raise utils.exc.ValidationError(errors={'daily_budget': [str(err)]})
