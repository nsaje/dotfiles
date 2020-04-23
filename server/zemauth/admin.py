from django.contrib import admin
from django.contrib import messages
from django.contrib.auth import admin as authadmin
from django.contrib.auth import forms
from django.contrib.auth.models import Permission
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _

import core.models
import utils.exc

from . import models


class EntityPermissionUserInline(admin.TabularInline):
    model = models.EntityPermission
    autocomplete_fields = ("agency", "account")
    extra = 0

    def get_queryset(self, request):
        qs = super(EntityPermissionUserInline, self).get_queryset(request)
        qs = qs.select_related("agency", "account")
        return qs


class UserCreationForm(forms.UserCreationForm):
    username = None

    class Meta:
        model = models.User
        fields = ("email",)


class UserChangeForm(forms.UserChangeForm):
    class Meta(forms.UserChangeForm.Meta):
        model = models.User
        field_classes = {"username": None}


class UserAdmin(authadmin.UserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    search_fields = ("email", "username", "first_name", "last_name", "outbrain_user_id")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("username", "first_name", "last_name", "outbrain_user_id")}),
        (
            _("Permissions"),
            {"fields": ("is_active", "is_staff", "is_superuser", "is_test_user", "groups", "user_permissions")},
        ),
        (_("SSPD sources"), {"fields": ["sspd_sources"]}),
        (_("SSPD sources and markets"), {"fields": ["sspd_sources_markets"]}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),)

    list_display = ("email", "username", "first_name", "last_name", "is_staff", "last_login")

    filter_horizontal = ("sspd_sources", "groups", "user_permissions")

    inlines = (EntityPermissionUserInline,)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "sspd_sources":
            kwargs["queryset"] = core.models.Source.objects.filter(deprecated=False)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        try:
            return super(UserAdmin, self).changeform_view(request, object_id, form_url, extra_context)
        except utils.exc.ValidationError as e:
            self.message_user(request, str(e.errors), level=messages.ERROR)
            return HttpResponseRedirect(request.path)


class InternalGroupAdmin(admin.ModelAdmin):
    search_fields = ("id", "name")

    def get_queryset(self, request):
        qs = super(InternalGroupAdmin, self).get_queryset(request)
        qs = qs.select_related("group")
        return qs


class PermissionAdmin(admin.ModelAdmin):
    search_fields = ("id", "name")

    def get_queryset(self, request):
        qs = super(PermissionAdmin, self).get_queryset(request)
        qs = qs.select_related("content_type")
        return qs


class EntityPermissionAdmin(admin.ModelAdmin):
    search_fields = ("id", "user__email", "agency__name", "account__name")
    list_display = ("id", "user", "agency", "account", "permission")
    autocomplete_fields = ("agency", "account")

    def get_queryset(self, request):
        qs = super(EntityPermissionAdmin, self).get_queryset(request)
        qs = qs.select_related("user", "agency", "account")
        return qs

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        try:
            return super(EntityPermissionAdmin, self).changeform_view(request, object_id, form_url, extra_context)
        except utils.exc.ValidationError as e:
            self.message_user(request, str(e.errors), level=messages.ERROR)
            return HttpResponseRedirect(request.path)


admin.site.register(models.User, UserAdmin)
admin.site.register(models.InternalGroup, InternalGroupAdmin)
admin.site.register(Permission, PermissionAdmin)
admin.site.register(models.EntityPermission, EntityPermissionAdmin)
