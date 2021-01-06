from django.db.models import F
from rest_framework import generics
from rest_framework.serializers import ValidationError

import core.models
import utils.exc
import zemauth.models
from utils import email_helper
from utils import metrics_compat
from utils.rest_common import authentication

from ... import base
from . import constants
from . import exceptions
from . import serializers
from . import service


class AgencyView(base.ServiceAPIBaseView):
    authentication_classes = (authentication.gen_oauth_authentication(constants.OUTBRAIN_SERVICE_NAME),)

    def post(self, request):
        serializer = serializers.AgencySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            new_agency = service.create_agency(request, **serializer.validated_data)
            metrics_compat.incr("serviceapi.salesforce.create_agency", 1, status="ok")
            return self.response_ok(serializers.AgencySerializer(new_agency).data, status=200)
        except utils.exc.ValidationError as e:
            metrics_compat.incr("serviceapi.salesforce.create_agency", 1, status="validation-error")
            raise ValidationError(e)

    def put(self, request, agency_id):
        agency = core.models.Agency.objects.get(id=agency_id, is_externally_managed=True)
        serializer = serializers.AgencySerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            updated_agency = service.update_agency(request, agency, **serializer.validated_data)
            metrics_compat.incr("serviceapi.salesforce.modify_agency", 1, status="ok")
            return self.response_ok(serializers.AgencySerializer(updated_agency).data, status=200)
        except utils.exc.ValidationError as e:
            metrics_compat.incr("serviceapi.salesforce.modify_agency", 1, status="validation-error")
            raise ValidationError(e)

    def get(self, request, agency_id):
        agency = core.models.Agency.objects.get(id=agency_id, is_externally_managed=True)
        return self.response_ok(serializers.AgencySerializer(agency).data, status=200)


class AgenciesView(base.ServiceAPIBaseView, generics.ListAPIView):
    authentication_classes = (authentication.gen_oauth_authentication(constants.OUTBRAIN_SERVICE_NAME),)
    serializer_class = serializers.AgencySerializer

    def get_queryset(self):
        queryset = core.models.Agency.objects.filter(is_externally_managed=True)
        date_range = serializers.DateRangeSerializer(data=self.request.query_params)
        date_range.is_valid(raise_exception=True)

        if not date_range.validated_data:
            raise exceptions.ListNoParametersProvided("Query parameters must be provided.")
        if date_range.validated_data.get("modified_dt_start"):
            queryset = queryset.filter(modified_dt__gte=date_range.validated_data["modified_dt_start"]).exclude(
                modified_dt=F("created_dt")
            )

        if date_range.validated_data.get("modified_dt_end"):
            queryset = queryset.filter(modified_dt__lte=date_range.validated_data["modified_dt_end"]).exclude(
                modified_dt=F("created_dt")
            )

        if date_range.validated_data.get("created_dt_start"):
            queryset = queryset.filter(created_dt__gte=date_range.validated_data["created_dt_start"])

        if date_range.validated_data.get("created_dt_end"):
            queryset = queryset.filter(created_dt__lte=date_range.validated_data["created_dt_end"])

        return set(queryset)


class AccountView(base.ServiceAPIBaseView):
    authentication_classes = (authentication.gen_oauth_authentication(constants.OUTBRAIN_SERVICE_NAME),)

    def post(self, request):
        serializer = serializers.AccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            new_account = service.create_account(request, **serializer.validated_data)
            metrics_compat.incr("serviceapi.salesforce.create_account", 1, status="ok")
            return self.response_ok(serializers.AccountSerializer(new_account).data, status=200)
        except utils.exc.ValidationError as e:
            metrics_compat.incr("serviceapi.salesforce.create_account", 1, status="validation-error")
            raise ValidationError(e)

    def put(self, request, account_id):
        account = core.models.Account.objects.get(
            id=account_id, agency__isnull=False, agency__is_externally_managed=True
        )
        serializer = serializers.AccountSerializer(data=request.data, partial=True, context={"account_id": account_id})
        serializer.is_valid(raise_exception=True)
        try:
            updated_account = service.update_account(request, account, **serializer.validated_data)
            metrics_compat.incr("serviceapi.salesforce.modify_account", 1, status="ok")
            return self.response_ok(serializers.AccountSerializer(updated_account).data, status=200)
        except utils.exc.ValidationError as e:
            metrics_compat.incr("serviceapi.salesforce.modify_account", 1, status="validation-error")
            raise ValidationError(e)

    def get(self, request, account_id):
        account = core.models.Account.objects.get(
            id=account_id, agency__isnull=False, agency__is_externally_managed=True
        )
        return self.response_ok(serializers.AccountSerializer(account).data, status=200)


class AccountsView(base.ServiceAPIBaseView, generics.ListAPIView):
    authentication_classes = (authentication.gen_oauth_authentication(constants.OUTBRAIN_SERVICE_NAME),)
    serializer_class = serializers.AccountSerializer

    def get_queryset(self):
        queryset = core.models.Account.objects.filter(agency__is_externally_managed=True)
        date_range = serializers.DateRangeSerializer(data=self.request.query_params)
        date_range.is_valid(raise_exception=True)

        if not date_range.validated_data:
            raise exceptions.ListNoParametersProvided("Query parameters must be provided.")
        if date_range.validated_data.get("modified_dt_start"):
            queryset = queryset.filter(modified_dt__gte=date_range.validated_data["modified_dt_start"]).exclude(
                modified_dt=F("created_dt")
            )

        if date_range.validated_data.get("modified_dt_end"):
            queryset = queryset.filter(modified_dt__lte=date_range.validated_data["modified_dt_end"]).exclude(
                modified_dt=F("created_dt")
            )

        if date_range.validated_data.get("created_dt_start"):
            queryset = queryset.filter(created_dt__gte=date_range.validated_data["created_dt_start"])

        if date_range.validated_data.get("created_dt_end"):
            queryset = queryset.filter(created_dt__lte=date_range.validated_data["created_dt_end"])

        return set(queryset)


class AccountArchiveView(base.ServiceAPIBaseView):
    authentication_classes = (authentication.gen_oauth_authentication(constants.OUTBRAIN_SERVICE_NAME),)

    def get(self, request, account_id):
        account = core.models.Account.objects.get(id=account_id, agency__is_externally_managed=True)
        account.archive(request)
        metrics_compat.incr("archive_account", 1, status="ok")
        return self.response_ok(serializers.AccountSerializer(account).data, status=200)


class UserView(base.ServiceAPIBaseView):
    authentication_classes = (authentication.gen_oauth_authentication(constants.OUTBRAIN_SERVICE_NAME),)

    def post(self, request):
        serializer = serializers.UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self._check_sales_office_and_alert(serializer.validated_data.get("sales_office"))
        try:
            new_user = service.create_user(**serializer.validated_data)
            metrics_compat.incr("serviceapi.salesforce.create_user", 1, status="ok")
            return self.response_ok(serializers.UserSerializer(new_user).data, status=200)
        except utils.exc.ValidationError as e:
            metrics_compat.incr("serviceapi.salesforce.create_user", 1, status="validation-error")
            raise ValidationError(e)

    def put(self, request, user_id):
        user = zemauth.models.User.objects.get(id=user_id, is_externally_managed=True)
        serializer = serializers.UserSerializer(data=request.data, partial=True, context={"user_id": user_id})
        serializer.is_valid(raise_exception=True)
        self._check_sales_office_and_alert(serializer.validated_data.get("sales_office"))
        try:
            updated_user = service.update_user(user, **serializer.validated_data)
            metrics_compat.incr("serviceapi.salesforce.modify_user", 1, status="ok")
            return self.response_ok(serializers.UserSerializer(updated_user).data, status=200)
        except utils.exc.ValidationError as e:
            metrics_compat.incr("serviceapi.salesforce.modify_user", 1, status="validation-error")
            raise ValidationError(e)

    def get(self, request, user_id):
        user = zemauth.models.User.objects.get(id=user_id, is_externally_managed=True)
        return self.response_ok(serializers.UserSerializer(user).data, status=200)

    @staticmethod
    def _check_sales_office_and_alert(sales_office):
        agency = constants.SALES_OFFICE_AGENCY_MAPPING.get(sales_office)
        if not agency:
            email_helper.send_unknown_sales_office_email(sales_office)


class UsersView(base.ServiceAPIBaseView, generics.ListAPIView):
    authentication_classes = (authentication.gen_oauth_authentication(constants.OUTBRAIN_SERVICE_NAME),)
    serializer_class = serializers.UserSerializer

    def get_queryset(self):
        queryset = zemauth.models.User.objects.filter(is_externally_managed=True)
        qpe = serializers.UserQueryParams(data=self.request.query_params)
        qpe.is_valid(raise_exception=True)
        email = qpe.validated_data.get("email")
        if email:
            queryset = queryset.filter(email__iexact=email)
        return set(queryset)
