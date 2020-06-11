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
from zemauth.features.entity_permission import EntityPermission
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
        account_id, agency_id, show_internal, keyword, calling_user = self._get_request_params(request)

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
        account_id, agency_id, show_internal, keyword, calling_user = self._get_request_params(request)
        account, agency = self._get_account_and_agency(calling_user, account_id, agency_id)

        serializer = serializers.CreateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        created_users = []

        with transaction.atomic():
            for user_data in request.data["users"]:
                user = self._get_or_create_user_by_email(user_data["email"], account, agency)

                self._validate_and_add_permissions_to_user(calling_user, account, agency, user, user_data)

                created_users.append(user)

        return self.response_ok(serializers.CreateUserSerializer({"users": created_users}).data)

    def get(self, request, user_id):
        requested_user = self._get_user(request, user_id)
        return self.response_ok(self.serializer(requested_user, context={"request": request}).data)

    def put(self, request, user_id):
        return self.response_ok(None)

    def remove(self, request, user_id):
        self._get_user_and_delete_permissions(request, user_id)

        return rest_framework.response.Response(None, status=rest_framework.status.HTTP_204_NO_CONTENT)

    def resendemail(self, request, user_id):
        return self.response_ok(None)

    def validate(self, request):
        return self.response_ok(None)

    def _get_user(self, request, user_id):
        account_id, agency_id, show_internal, keyword, calling_user = self._get_request_params(request)

        agency: Agency = None
        account: Account = None
        requested_user: ZemUser = None

        if account_id is not None:
            account = zemauth.access.get_account(calling_user, Permission.USER, account_id)
            requested_user = ZemUser.objects.filter_by_account(account).get(pk=user_id)
        elif agency_id is not None:
            agency = zemauth.access.get_agency(calling_user, Permission.USER, agency_id)
            requested_user = ZemUser.objects.filter_by_agency_and_related_accounts(agency).get(pk=user_id)
        else:
            raise ValidationError(errors={"non_field_errors": "Either agency id or account id must be provided."})

        self._augment_user(calling_user, requested_user, agency, account)
        return requested_user

    def _get_user_and_delete_permissions(self, request, user_id):
        requested_user = self._get_user(request, user_id)
        requested_user.entity_permissions.all().delete()

        return requested_user

    def _get_request_params(self, request):
        calling_user: ZemUser = request.user
        query_params = serializers.UserQueryParamsExpectations(data=request.query_params)
        query_params.is_valid(raise_exception=True)
        agency_id: int = query_params.validated_data.get("agency_id")
        account_id: int = query_params.validated_data.get("account_id")
        show_internal: bool = query_params.validated_data.get("show_internal")
        keyword: str = query_params.validated_data.get("keyword")
        return account_id, agency_id, show_internal, keyword, calling_user

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

    def _get_account_and_agency(self, calling_user, account_id, agency_id):
        account: Account = None
        if account_id is not None:
            account = zemauth.access.get_account(calling_user, Permission.USER, account_id)
            agency = account.agency
        elif agency_id is not None:
            agency = zemauth.access.get_agency(calling_user, Permission.USER, agency_id)
        else:
            raise ValidationError(errors={"non_field_errors": "Either agency id or account id must be provided."})
        return account, agency

    def _validate_permissions(self, calling_user, agency, user_email, user_permissions):
        if len(list(filter(lambda ep: ep["permission"] == Permission.READ, user_permissions))) == 0:
            raise ValidationError(
                errors={"non_field_errors": u"User with email %s must have READ permission" % user_email}
            )

        has_account_permission: bool = len(
            list(filter(lambda permission: "account_id" in permission, user_permissions))
        ) > 0
        has_agency_permission: bool = len(
            list(filter(lambda permission: "agency_id" in permission, user_permissions))
        ) > 0

        if has_account_permission and has_agency_permission:
            raise ValidationError(errors={"non_field_errors": "Mixing account and agency permissions is not allowed."})

        for permission in user_permissions:
            if "account_id" in permission:
                permission_account = zemauth.access.get_account(calling_user, Permission.USER, permission["account_id"])
                if permission_account.agency is None or agency.id != permission_account.agency.id:
                    raise ValidationError(errors={"non_field_errors": "Account does not belong to the correct agency"})
            elif "agency_id" in permission:
                if agency.id != permission["agency_id"]:
                    raise ValidationError(errors={"non_field_errors": "Incorrect agency ID"})
            else:
                raise ValidationError(
                    errors={
                        "non_field_errors": "Either agency id or account id must be provided for each entity permission."
                    }
                )

    def _get_or_create_user_by_email(self, user_email, account, agency):
        user_qs = ZemUser.objects.filter(email=user_email)
        user = list(user_qs)[0] if user_qs.exists() else None
        if user:
            if account is not None:
                user_already_exists_in_scope = (
                    ZemUser.objects.filter_by_account(account).filter(email=user_email).exists()
                )
            elif agency is not None:
                user_already_exists_in_scope = (
                    ZemUser.objects.filter_by_agency_and_related_accounts(agency).filter(email=user_email).exists()
                )

            if user_already_exists_in_scope:
                raise ValidationError(
                    errors={"non_field_errors": u"User with email address %s already exists." % user_email}
                )
        else:
            user = ZemUser.objects.create(email=user_email)

        return user

    def _validate_and_add_permissions_to_user(self, calling_user, account, agency, user, user_data):
        email = user_data["email"]
        entity_permissions = user_data["entity_permissions"]
        self._validate_permissions(calling_user, agency, email, entity_permissions)
        self._add_permissions_to_user(calling_user, account, agency, user, entity_permissions)

    def _add_permissions_to_user(self, calling_user, account, agency, requested_user, permissions):
        for permission in permissions:
            if "account_id" in permission:
                permission_account = zemauth.access.get_account(calling_user, Permission.USER, permission["account_id"])
                EntityPermission.objects.create(requested_user, permission["permission"], account=permission_account)
            elif "agency_id" in permission:
                EntityPermission.objects.create(requested_user, permission["permission"], agency=agency)
        self._augment_user(calling_user, requested_user, agency, account)
