from rest_framework import serializers

import core.models
import dash.constants


class SeatSerializer(serializers.Serializer):
    agency_id = serializers.IntegerField(source="agency.id", allow_null=True)
    agency_name = serializers.CharField(source="agency.name", allow_null=True)
    account_id = serializers.IntegerField(source="id")
    account_name = serializers.CharField(source="name")
    ob_sales_representative_id = serializers.SerializerMethodField()
    ob_account_manager_id = serializers.SerializerMethodField()
    is_zms_account = serializers.SerializerMethodField()

    def get_is_zms_account(self, obj):
        return core.models.Account.objects.filter_by_business(dash.constants.Business.ZMS).filter(id=obj.id).exists()

    def get_ob_sales_representative_id(self, obj):
        if self.get_is_zms_account(obj):
            if obj.settings.default_sales_representative:
                return obj.settings.default_sales_representative.outbrain_user_id
        else:
            if obj.settings.ob_sales_representative:
                return obj.settings.ob_sales_representative.outbrain_user_id

    def get_ob_account_manager_id(self, obj):
        if self.get_is_zms_account(obj):
            if obj.settings.default_account_manager:
                return obj.settings.default_account_manager.outbrain_user_id
        else:
            if obj.settings.ob_account_manager:
                return obj.settings.ob_account_manager.outbrain_user_id
