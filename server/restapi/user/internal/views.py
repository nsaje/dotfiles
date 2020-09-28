import rest_framework.response
import rest_framework.status
from django.contrib.auth import models as auth_models
from django.db import transaction
from django.db.models import Q
from rest_framework import permissions

import zemauth.access
from core.models import Account
from core.models import Agency
from restapi.common.pagination import StandardPagination
from restapi.common.views_base import RESTAPIBaseViewSet
from utils.email_helper import send_new_user_email
from utils.exc import ValidationError
from zemauth.features.entity_permission import EntityPermission
from zemauth.features.entity_permission import Permission
from zemauth.features.entity_permission.constants import REPORTING_PERMISSIONS
from zemauth.models import User as ZemUser
from zemauth.models.user.exceptions import MissingReadPermission
from zemauth.models.user.exceptions import MissingRequiredPermission
from zemauth.models.user.exceptions import MixedPermissionLevels

from . import serializers


class CurrentUserViewSet(RESTAPIBaseViewSet):
    serializer = serializers.CurrentUserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def current(self, request):
        return self.response_ok(serializers.CurrentUserSerializer(request.user, context={"request": request}).data)


class UserViewSet(RESTAPIBaseViewSet):
    serializer = serializers.UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

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
        paginated_users = paginator.paginate_queryset(users.distinct(), request)
        for requested_user in paginated_users:
            self._augment_user(requested_user, request, account, agency)

        return paginator.get_paginated_response(self.serializer(paginated_users, many=True).data)

    def create(self, request):
        serializer = self.serializer(
            data=request.data, many=isinstance(request.data, list), context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        changes = serializer.validated_data

        if isinstance(changes, list):
            data = self._create_multiple(request, changes)
        else:
            data = self._create_single(request, changes)

        return self.response_ok(self.serializer(data, many=isinstance(data, list)).data, status=201)

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
        account, agency, show_internal, keyword, calling_user = self._get_request_params(request)
        requested_user = zemauth.access.get_user(calling_user, user_id, account, agency, Permission.USER)

        send_new_user_email(requested_user, request)
        return self.response_ok(None)

    def validate(self, request):
        serializer = self.serializer(
            data=request.data, partial=True, many=isinstance(request.data, list), context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
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

    def _create_multiple(self, request, changes):
        account, agency, show_internal, keyword, calling_user = self._get_request_params(request)
        created_users = []
        users = []

        try:
            with transaction.atomic():
                for user_data in changes:
                    user, created = self._handle_user(request, agency, account, user_data)
                    users.append(user)
                    if created:
                        created_users.append(user)
        except (MixedPermissionLevels, MissingReadPermission, MissingRequiredPermission) as err:
            raise ValidationError(str(err))

        for user in created_users:
            send_new_user_email(user, request)

        return users

    def _create_single(self, request, changes):
        account, agency, show_internal, keyword, calling_user = self._get_request_params(request)

        try:
            with transaction.atomic():
                user, created = self._handle_user(request, agency, account, changes)
        except (MixedPermissionLevels, MissingReadPermission, MissingRequiredPermission) as err:
            raise ValidationError(str(err))

        if created:
            send_new_user_email(user, request)

        return user

    def _handle_user(self, request, agency, account, changes):
        created = False

        user = ZemUser.objects.filter(email__iexact=changes["email"]).first()
        if not user:
            user = ZemUser.objects.create_user(changes["email"])
            self._add_user_to_groups(user)
            created = True
        user.update(**changes)
        user.set_entity_permissions(request, account, agency, changes.get("entity_permissions"))
        self._augment_user(user, request, account, agency)

        return user, created

    @classmethod
    def _augment_user(cls, requested_user: ZemUser, request, account: Account, agency: Agency):
        entity_permissions = requested_user.get_entity_permissions(request, account, agency)
        requested_user_reporting_permissions = requested_user.entitypermission_set.filter(
            permission__in=REPORTING_PERMISSIONS
        )
        for entity_permission in entity_permissions:
            cls._augment_entity_permission(entity_permission, requested_user_reporting_permissions, request)
        requested_user.entity_permissions = entity_permissions

    @classmethod
    def _augment_entity_permission(
        cls, entity_permission: EntityPermission, requested_user_reporting_permissions, request
    ):
        calling_user: ZemUser = request.user
        if not calling_user.has_greater_or_equal_permission(entity_permission) or (
            entity_permission.is_reporting_permission()
            and cls._user_has_hidden_reporting_permissions(
                calling_user, requested_user_reporting_permissions, entity_permission
            )
        ):
            entity_permission.readonly = True

    @classmethod
    def _user_has_hidden_reporting_permissions(
        cls, calling_user: ZemUser, requested_user_reporting_permissions, entity_permission: EntityPermission
    ) -> bool:
        return any(
            filter(
                lambda ep: (
                    ep.agency_id == entity_permission.agency_id and ep.account_id == entity_permission.account_id
                )
                and not calling_user.has_greater_or_equal_permission(ep),
                requested_user_reporting_permissions,
            )
        )

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

    @staticmethod
    def _add_user_to_groups(user):
        perm = auth_models.Permission.objects.get(codename="this_is_public_group")
        group = auth_models.Group.objects.filter(permissions=perm).first()
        if group is not None:
            group.user_set.add(user)
