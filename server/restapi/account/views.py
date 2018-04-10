from restapi.views import RESTAPIBaseViewSet

import restapi.access
from . import serializers
import core.entity
import dash.constants


UPDATABLE_SETTINGS_FIELDS = (
    'name',
    'whitelist_publisher_groups',
    'blacklist_publisher_groups',
)


class AccountViewSet(RESTAPIBaseViewSet):

    def get(self, request, account_id):
        account = restapi.access.get_account(request.user, account_id)
        return self.response_ok(serializers.AccountSerializer(account).data)

    def put(self, request, account_id):
        account = restapi.access.get_account(request.user, account_id)
        serializer = serializers.AccountSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        settings_updates = serializer.validated_data.get('settings')
        if settings_updates:
            update = {key: value for key, value in list(settings_updates.items()) if key in UPDATABLE_SETTINGS_FIELDS}
            account.settings.update(request, **update)
        return self.response_ok(serializers.AccountSerializer(account).data)

    def list(self, request):
        accounts = core.entity.Account.objects.all().filter_by_user(request.user)
        return self.response_ok(serializers.AccountSerializer(accounts, many=True).data)

    def create(self, request):
        serializer = serializers.AccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        agency = None
        agency_id = serializer.validated_data.get('agency_id')
        if agency_id:
            agency = restapi.access.get_agency(request.user, agency_id)

        new_account = core.entity.Account.objects.create(
            request,
            name=serializer.validated_data['settings']['name'],
            agency=agency,
            currency=dash.constants.Currency.USD,
        )

        settings_updates = serializer.validated_data.get('settings')
        if settings_updates:
            update = {key: value for key, value in list(settings_updates.items()) if key in UPDATABLE_SETTINGS_FIELDS}
            new_account.settings.update(request, **update)
        return self.response_ok(serializers.AccountSerializer(new_account).data, status=201)
