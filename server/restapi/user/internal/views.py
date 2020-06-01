from django.db.models import Q
from rest_framework import permissions

import zemauth.access
from core.models import Account
from core.models import Agency
from restapi.common.pagination import StandardPagination
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
        calling_user: ZemUser = request.user

        query_params = serializers.UserQueryParamsExpectations(data=request.query_params)
        query_params.is_valid(raise_exception=True)

        agency_id: int = query_params.validated_data.get("agency_id")
        account_id: int = query_params.validated_data.get("account_id")
        show_internal: bool = query_params.validated_data.get("show_internal")
        keyword: str = query_params.validated_data.get("keyword")

        agency: Agency = None
        account: Account = None

        all_users = ZemUser.objects.order_by("first_name", "last_name")

        if account_id is not None:
            account = zemauth.access.get_account(calling_user, Permission.USER, account_id)
            users = all_users.filter_by_account(account)
        elif agency_id is not None:
            agency = zemauth.access.get_agency(calling_user, Permission.USER, agency_id)
            users = all_users.filter_by_agency_and_related_accounts(agency)
        else:
            raise ValidationError(errors={"non_field_errors": "Either agency id or account id must be provided."})

        if show_internal:
            if calling_user.has_perm_on_all_entities(Permission.USER):
                users |= all_users.filter_by_internal()
            else:
                raise ValidationError(errors={"non_field_errors": "You are not authorized to view internal users."})

        if keyword:
            users = users.filter(
                Q(id__icontains=keyword)
                | Q(email__icontains=keyword)
                | Q(first_name__icontains=keyword)
                | Q(last_name__icontains=keyword)
            )

        paginator = StandardPagination()
        paginated_users = paginator.paginate_queryset(users, request)
        for requested_user in paginated_users:
            self._augment_user(calling_user, requested_user, agency, account)

        return paginator.get_paginated_response(self.serializer(paginated_users, many=True).data)

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

        requested_user.entity_permissions = (
            requested_user.entitypermission_set.filter_by_accounts(callers_accounts_on_agency)
            | requested_user.entitypermission_set.filter_by_agency(requested_agency)
            | requested_user.entitypermission_set.filter_by_internal()
        )
