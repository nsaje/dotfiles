from rest_framework import permissions

import zemauth.access
from core.models import Account
from core.models import Agency
from restapi.common.views_base import RESTAPIBaseViewSet
from utils.exc import ValidationError
from zemauth.features.entity_permission import Permission
from zemauth.models import User as ZemUser

from . import serializers


class CanUseEntityPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.has_perm("zemauth.fea_use_entity_permission"))


class UserViewSet(RESTAPIBaseViewSet):
    serializer = serializers.UserSerializer
    permission_classes = (permissions.IsAuthenticated, CanUseEntityPermission)

    def list(self, request):
        return self.response_ok(None)

    def create(self, request):
        return self.response_ok(None)

    def get(self, request, user_id):
        calling_user: ZemUser = request.user
        requested_user: ZemUser = None

        query_params = serializers.UserQueryParamsExpectations(data=request.query_params)
        query_params.is_valid(raise_exception=True)

        agency_id: int = query_params.validated_data.get("agency_id")
        account_id: int = query_params.validated_data.get("account_id")

        agency: Agency = None
        account: Account = None

        if account_id is not None:
            account = zemauth.access.get_account(calling_user, Permission.USER, account_id)
            requested_user = ZemUser.objects.filter_by_account(account).get(pk=user_id)
        elif agency_id is not None:
            agency = zemauth.access.get_agency(calling_user, Permission.USER, agency_id)
            requested_user = ZemUser.objects.filter_by_agency_and_related_accounts(agency).get(pk=user_id)
        else:
            raise ValidationError(errors={"non_field_errors": "Either agency id or account id must be provided."})

        self._augment_user(calling_user, requested_user, agency, account)
        return self.response_ok(self.serializer(requested_user, context={"request": request}).data)

    def put(self, request, user_id):
        return self.response_ok(None)

    def remove(self, request, user_id):
        return self.response_ok(None)

    def resendemail(self, request, user_id):
        return self.response_ok(None)

    def validate(self, request):
        return self.response_ok(None)

    @staticmethod
    def _augment_user(calling_user: ZemUser, requested_user: ZemUser, agency: Agency, account: Account):
        requested_agency: Agency = account.agency if account else agency

        callers_accounts = zemauth.access.get_accounts(calling_user, Permission.USER)
        callers_accounts_on_agency = callers_accounts.filter(agency=requested_agency)

        requested_user.entity_permissions = requested_user.entitypermission_set.filter_by_accounts(
            callers_accounts_on_agency
        ) | requested_user.entitypermission_set.filter_by_agency(requested_agency)
