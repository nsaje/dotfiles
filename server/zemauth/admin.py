from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import admin as authadmin, forms
from django.contrib.auth.models import Permission

from . import models


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

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("username", "first_name", "last_name")}),
        (
            _("Permissions"),
            {"fields": ("is_active", "is_staff", "is_superuser", "is_test_user", "groups", "user_permissions")},
        ),
        (_("SSPD sources"), {"fields": ["sspd_sources"]}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),)

    list_display = ("email", "username", "first_name", "last_name", "is_staff", "last_login")

    filter_horizontal = ("groups", "user_permissions", "sspd_sources")

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "sspd_sources":
            kwargs["queryset"] = models.Source.objects.filter(deprecated=False)
        return super().formfield_for_manytomany(db_field, request, **kwargs)


class InternalGroupAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super(InternalGroupAdmin, self).get_queryset(request)
        qs = qs.select_related("group")
        return qs


class PermissionAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super(PermissionAdmin, self).get_queryset(request)
        qs = qs.select_related("content_type")
        return qs


admin.site.register(models.User, UserAdmin)
admin.site.register(models.InternalGroup, InternalGroupAdmin)
admin.site.register(Permission, PermissionAdmin)
