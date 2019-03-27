from django import forms
from django.contrib import admin
from django.contrib.postgres.forms import SimpleArrayField
from django.template.defaultfilters import truncatechars

import core.models

from . import models


class DemoMappingAdminForm(forms.ModelForm):
    real_account = forms.ModelChoiceField(queryset=core.models.Account.objects.order_by("name"))
    demo_campaign_name_pool = SimpleArrayField(
        forms.CharField(), delimiter="\n", widget=forms.Textarea, help_text="Put every demo name in a separate line"
    )
    demo_ad_group_name_pool = SimpleArrayField(
        forms.CharField(), delimiter="\n", widget=forms.Textarea, help_text="Put every demo name in a separate line"
    )


class DemoMappingAdmin(admin.ModelAdmin):
    list_display = ("real_account", "demo_account_name", "demo_campaign_name_pool_", "demo_ad_group_name_pool_")
    form = DemoMappingAdminForm
    autocomplete_fields = ("real_account",)

    def demo_campaign_name_pool_(self, obj):
        return truncatechars(", ".join(obj.demo_campaign_name_pool), 70)

    def demo_ad_group_name_pool_(self, obj):
        return truncatechars(", ".join(obj.demo_ad_group_name_pool), 70)


admin.site.register(models.DemoMapping, DemoMappingAdmin)
