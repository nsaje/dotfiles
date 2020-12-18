from collections import OrderedDict

import rest_framework.serializers
from drf_base64.fields import Base64ImageField

import dash.constants
import restapi.account.v1.serializers
import restapi.directdeal.internal.serializers
import restapi.serializers.base
import restapi.serializers.deals
import restapi.serializers.fields
import restapi.serializers.hack
import restapi.serializers.user
import utils.exc
import zemauth.models
from zemauth.features.entity_permission import Permission


class AccountMediaSourceSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    id = restapi.serializers.fields.IdField()
    name = restapi.serializers.fields.PlainCharField()
    released = rest_framework.serializers.BooleanField(default=False)
    deprecated = rest_framework.serializers.BooleanField(default=False)


class ExtraDataAgencySerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    id = restapi.serializers.fields.IdField(required=False)
    name = restapi.serializers.fields.PlainCharField(required=False)
    sales_representative = restapi.serializers.fields.IdField(required=False)
    cs_representative = restapi.serializers.fields.IdField(required=False)
    ob_sales_representative = restapi.serializers.fields.IdField(required=False)
    ob_account_manager = restapi.serializers.fields.IdField(required=False)
    default_account_type = restapi.serializers.fields.DashConstantField(
        dash.constants.AccountType, default=dash.constants.AccountType.UNKNOWN, required=False
    )


class ExtraDataSerializer(restapi.serializers.base.RESTAPIBaseSerializer):
    archived = rest_framework.serializers.BooleanField(default=False, required=False)
    can_restore = rest_framework.serializers.BooleanField(default=False, required=False)
    is_externally_managed = rest_framework.serializers.BooleanField(default=False, required=False)
    agencies = rest_framework.serializers.ListField(child=ExtraDataAgencySerializer(), default=[], allow_empty=True)
    account_managers = rest_framework.serializers.ListField(
        child=restapi.serializers.user.UserSerializer(), default=[], allow_empty=True
    )
    sales_representatives = rest_framework.serializers.ListField(
        child=restapi.serializers.user.UserSerializer(), default=[], allow_empty=True
    )
    cs_representatives = rest_framework.serializers.ListField(
        child=restapi.serializers.user.UserSerializer(), default=[], allow_empty=True
    )
    ob_representatives = rest_framework.serializers.ListField(
        child=restapi.serializers.user.UserSerializer(), default=[], allow_empty=True
    )
    hacks = rest_framework.serializers.ListField(
        child=restapi.serializers.hack.HackSerializer(), default=[], allow_empty=True
    )
    deals = rest_framework.serializers.ListField(
        child=restapi.serializers.deals.DealSerializer(), default=[], allow_empty=True
    )
    available_media_sources = rest_framework.serializers.ListField(
        child=AccountMediaSourceSerializer(), default=[], allow_empty=True
    )


class AccountSerializer(
    restapi.serializers.serializers.EntityPermissionedFieldsMixin, restapi.account.v1.serializers.AccountSerializer
):
    class Meta:
        permissioned_fields = {
            "account_type": "zemauth.can_modify_account_type",
            "default_account_manager": "zemauth.can_modify_account_manager",
            "default_sales_representative": "zemauth.can_set_account_sales_representative",
            "default_cs_representative": "zemauth.can_set_account_cs_representative",
            "ob_sales_representative": "zemauth.can_set_account_ob_representative",
            "ob_account_manager": "zemauth.can_set_account_ob_representative",
            "salesforce_url": "zemauth.can_see_salesforce_url",
        }
        entity_permissioned_fields = {
            "config": {
                "entity_id_getter_fn": lambda data: data.get("id"),
                "entity_access_fn": zemauth.access.get_account,
            },
            "fields": {"deals": Permission.WRITE},
        }

    agency_id = restapi.serializers.fields.IdField(allow_null=False)
    account_type = restapi.serializers.fields.DashConstantField(
        dash.constants.AccountType,
        source="settings.account_type",
        default=dash.constants.AccountType.UNKNOWN,
        required=False,
    )
    default_account_manager = restapi.serializers.fields.IdField(
        source="settings.default_account_manager", required=False, allow_null=True
    )
    default_sales_representative = restapi.serializers.fields.IdField(
        source="settings.default_sales_representative", required=False, allow_null=True
    )
    default_cs_representative = restapi.serializers.fields.IdField(
        source="settings.default_cs_representative", required=False, allow_null=True
    )
    ob_sales_representative = restapi.serializers.fields.IdField(
        source="settings.ob_sales_representative", required=False, allow_null=True
    )
    ob_account_manager = restapi.serializers.fields.IdField(
        source="settings.ob_account_manager", required=False, allow_null=True
    )
    auto_add_new_sources = rest_framework.serializers.BooleanField(
        source="settings.auto_add_new_sources", default=False, required=False
    )
    salesforce_url = restapi.serializers.fields.PlainCharField(
        source="settings.salesforce_url", max_length=255, required=False, allow_null=True, allow_blank=True
    )
    allowed_media_sources = rest_framework.serializers.ListField(
        child=AccountMediaSourceSerializer(), default=[], allow_empty=True
    )
    deals = rest_framework.serializers.ListSerializer(
        child=restapi.directdeal.internal.serializers.DirectDealSerializer(), default=[], allow_empty=True
    )
    default_icon_url = rest_framework.serializers.URLField(required=False, allow_null=True, allow_blank=True)
    default_icon_base64 = Base64ImageField(required=False, allow_null=True, write_only=True)

    def validate_default_account_manager(self, value):
        if value is None:
            return value
        if not zemauth.models.User.objects.filter(pk=value).exists():
            raise rest_framework.serializers.ValidationError(["Invalid account manager."])
        return value

    def validate_default_sales_representative(self, value):
        if value is None:
            return value
        if not zemauth.models.User.objects.get_users_with_perm("campaign_settings_sales_rep").filter(pk=value).exists():
            raise rest_framework.serializers.ValidationError(["Invalid sales representative."])
        return value

    def validate_default_cs_representative(self, value):
        if value is None:
            return value
        if not zemauth.models.User.objects.get_users_with_perm("campaign_settings_cs_rep").filter(pk=value).exists():
            raise rest_framework.serializers.ValidationError(["Invalid CS representative."])
        return value

    def validate_ob_sales_representative(self, value):
        if value is None:
            return value
        if not zemauth.models.User.objects.get_users_with_perm("can_be_ob_representative").filter(pk=value).exists():
            raise rest_framework.serializers.ValidationError(["Invalid OB representative."])
        return value

    def validate_ob_account_manager(self, value):
        if value is None:
            return value
        if not zemauth.models.User.objects.get_users_with_perm("can_be_ob_representative").filter(pk=value).exists():
            raise rest_framework.serializers.ValidationError(["Invalid OB Account manager."])
        return value

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        settings_field = "settings"
        if settings_field not in value.keys():
            value[settings_field] = {}

        if "default_account_manager" in value[settings_field].keys():
            default_account_manager = self.to_internal_value_default_account_manager(
                data.get("default_account_manager")
            )
            value[settings_field]["default_account_manager"] = default_account_manager

        if "default_sales_representative" in value[settings_field].keys():
            default_sales_representative = self.to_internal_value_default_sales_representative(
                data.get("default_sales_representative")
            )
            value[settings_field]["default_sales_representative"] = default_sales_representative

        if "default_cs_representative" in value[settings_field].keys():
            default_cs_representative = self.to_internal_value_default_cs_representative(
                data.get("default_cs_representative")
            )
            value[settings_field]["default_cs_representative"] = default_cs_representative

        if "ob_sales_representative" in value[settings_field].keys():
            ob_sales_representative = self.to_internal_value_ob_representative(data.get("ob_sales_representative"))
            value[settings_field]["ob_sales_representative"] = ob_sales_representative

        if "ob_account_manager" in value[settings_field].keys():
            ob_account_manager = self.to_internal_value_ob_representative(data.get("ob_account_manager"))
            value[settings_field]["ob_account_manager"] = ob_account_manager

        return value

    def to_internal_value_default_account_manager(self, data):
        if data is None:
            return data
        return zemauth.models.User.objects.get(pk=data)

    def to_internal_value_default_sales_representative(self, data):
        if data is None:
            return data
        return zemauth.models.User.objects.get_users_with_perm("campaign_settings_sales_rep").get(pk=data)

    def to_internal_value_default_cs_representative(self, data):
        if data is None:
            return data
        return zemauth.models.User.objects.get_users_with_perm("campaign_settings_cs_rep").get(pk=data)

    def to_internal_value_ob_representative(self, data):
        if data is None:
            return data
        return zemauth.models.User.objects.get_users_with_perm("can_be_ob_representative").get(pk=data)

    def has_entity_permission(
        self, user: zemauth.models.User, permission: Permission, config: OrderedDict, data: OrderedDict
    ) -> bool:
        account_id = data.get("id")
        if account_id is not None:
            return super().has_entity_permission(user, permission, config, data)

        agency_id = data.get("agency_id")
        if agency_id is not None:
            try:
                zemauth.access.get_agency(user, permission, agency_id)
                return True
            except utils.exc.MissingDataError:
                return False

        return False
