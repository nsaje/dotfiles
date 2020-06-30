import rest_framework.response
import rest_framework.status
from django.db import transaction
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
from zemauth.models.user.exceptions import MissingReadPermission
from zemauth.models.user.exceptions import MissingRequiredPermission
from zemauth.models.user.exceptions import MixedPermissionLevels

from . import serializers


class CanUseEntityPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.has_perm("zemauth.fea_use_entity_permission"))


class UserViewSet(RESTAPIBaseViewSet):
    serializer = serializers.UserSerializer
    permission_classes = (permissions.IsAuthenticated, CanUseEntityPermission)

    def list(self, request):
        account, agency, show_internal, keyword, calling_user = self._get_request_params(request)

        all_users = ZemUser.objects.order_by("first_name", "last_name")

        if account is not None:
            users = all_users.filter_by_account(account)
        elif agency is not None:
            users = all_users.filter_by_agency_and_related_accounts(agency)

        if show_internal:
            if calling_user.has_perm_on_all_entities(Permission.USER):
                users |= all_users.filter_by_internal()
            else:
                raise ValidationError("You are not authorized to view internal users.")

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
            self._augment_user(requested_user, request, account, agency)

        return paginator.get_paginated_response(self.serializer(paginated_users, many=True).data)

    def create(self, request):
        account, agency, show_internal, keyword, calling_user = self._get_request_params(request)

        serializer = serializers.CreateUserSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        changes = serializer.validated_data

        created_users = []

        try:
            with transaction.atomic():
                for user_data in changes.get("users"):
                    user = ZemUser.objects.get_or_create_user_by_email(user_data["email"])
                    user.update(**user_data)
                    user.set_entity_permissions(request, account, agency, user_data.get("entity_permissions"))
                    self._augment_user(user, request, account, agency)

                    created_users.append(user)

        except (MixedPermissionLevels, MissingReadPermission, MissingRequiredPermission) as err:
            raise ValidationError(str(err))

        return self.response_ok(serializers.CreateUserSerializer({"users": created_users}).data)

    def get(self, request, user_id):
        account, agency, show_internal, keyword, calling_user = self._get_request_params(request)

        requested_user = zemauth.access.get_user(calling_user, user_id, account, agency)
        self._augment_user(requested_user, request, account, agency)

        return self.response_ok(self.serializer(requested_user, context={"request": request}).data)

    def put(self, request, user_id):
        account, agency, show_internal, keyword, calling_user = self._get_request_params(request)

        serializer = serializers.UserSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user_data = serializer.validated_data

        try:
            with transaction.atomic():
                requested_user = zemauth.access.get_user(calling_user, user_id, account, agency, Permission.USER)
                requested_user.update(**user_data)
                requested_user.set_entity_permissions(request, account, agency, user_data.get("entity_permissions"))
                self._augment_user(requested_user, request, account, agency)

        except (MixedPermissionLevels, MissingReadPermission, MissingRequiredPermission) as err:
            raise ValidationError(str(err))

        return self.response_ok(self.serializer(requested_user, context={"request": request}).data)

    def remove(self, request, user_id):
        account, agency, show_internal, keyword, calling_user = self._get_request_params(request)

        requested_user = zemauth.access.get_user(calling_user, user_id, account, agency, Permission.USER)
        requested_user.delete_entity_permissions(request, account, agency)

        return rest_framework.response.Response(None, status=rest_framework.status.HTTP_204_NO_CONTENT)

    def resendemail(self, request, user_id):
        return self.response_ok(None)

    def validate(self, request):
        return self.response_ok(None)

    def _get_request_params(self, request):
        calling_user: ZemUser = request.user
        query_params = serializers.UserQueryParamsExpectations(data=request.query_params)
        query_params.is_valid(raise_exception=True)
        agency_id: int = query_params.validated_data.get("agency_id")
        account_id: int = query_params.validated_data.get("account_id")
        show_internal: bool = query_params.validated_data.get("show_internal")
        keyword: str = query_params.validated_data.get("keyword")

        account, agency = self._get_account_and_agency(calling_user, account_id, agency_id)

        return account, agency, show_internal, keyword, calling_user

    @staticmethod
    def _augment_user(requested_user: ZemUser, request, account: Account, agency: Agency):
        requested_user.entity_permissions = requested_user.get_entity_permissions(request, account, agency)

    @staticmethod
    def _get_account_and_agency(calling_user, account_id, agency_id):
        account: Account = None
        if account_id is not None:
            account = zemauth.access.get_account(calling_user, Permission.USER, account_id)
            agency = account.agency
        elif agency_id is not None:
            agency = zemauth.access.get_agency(calling_user, Permission.USER, agency_id)
        else:
            raise ValidationError("Either agency id or account id must be provided.")
        return account, agency
