from django.conf.urls import url
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html

from . import models
from . import service


class RulesDailyJobLogAdmin(admin.ModelAdmin):
    model = models.RulesDailyJobLog
    list_display = ("created_dt",)
    ordering = ("-created_dt",)
    list_display_links = None


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
        "rule_actions",
        "ad_groups_included_ids",
        "campaigns_included_ids",
        "accounts_included_ids",
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
    exclude = ("ad_groups_included", "campaigns_included", "accounts_included")

    def ad_groups_included_ids(self, obj=None):
        if obj is None:
            return []
        return list(obj.ad_groups_included.all().values_list("id", flat=True))

    def campaigns_included_ids(self, obj=None):
        if obj is None:
            return []
        return list(obj.campaigns_included.all().values_list("id", flat=True))

    def accounts_included_ids(self, obj=None):
        if obj is None:
            return []
        return list(obj.accounts_included.all().values_list("id", flat=True))

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            url(r"^(?P<rule_id>.+)/run/$", self.admin_site.admin_view(self.run_rule), name="automation-run-rule")
        ]
        return custom_urls + urls

    def rule_actions(self, rule):
        if rule.id is None:
            return "Rule not yet created"
        return format_html('<a class="button" href="{}">Run</a>', reverse("admin:automation-run-rule", args=[rule.id]))

    rule_actions.short_description = "Rule Actions"

    def run_rule(self, request, rule_id, *args, **kwargs):
        rule = self.get_object(request, rule_id)

        service.execute_rules([rule])
        self.message_user(request, "Rule ran successfully. See history for details.")

        url = reverse("admin:automation_rule_change", args=[rule.id], current_app=self.admin_site.name)
        return HttpResponseRedirect(url)
