from django.contrib import admin

from . import models


class RuleConditionAdmin(admin.TabularInline):
    model = models.RuleCondition

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class RuleHistoryAdmin(admin.TabularInline):
    model = models.RuleHistory
    readonly_fields = ("ad_group_id", "ad_group", "status", "changes_text", "changes", "created_dt")
    ordering = ("-created_dt",)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class RuleAdmin(admin.ModelAdmin):
    inlines = [RuleConditionAdmin, RuleHistoryAdmin]
    search_fields = ("agency", "name", "target_type", "action_type")
    list_display = (
        "id",
        "agency",
        "name",
        "state",
        "target_type",
        "action_type",
        "notification_type",
        "created_dt",
        "created_by",
    )
    readonly_fields = (
        "agency",
        "name",
        "ad_groups_included_ids",
        "target_type",
        "action_type",
        "send_email_subject",
        "send_email_body",
        "send_email_recipients",
        "publisher_group",
        "change_step",
        "change_limit",
        "cooldown",
        "window",
        "notification_type",
        "notification_recipients",
        "created_dt",
        "created_by",
        "modified_by",
    )
    raw_id_fields = ("created_by", "modified_by")
    exclude = ("ad_groups_included",)

    def ad_groups_included_ids(self, obj=None):
        if obj is None:
            return []
        return list(obj.ad_groups_included.all().values_list("id", flat=True))

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True
