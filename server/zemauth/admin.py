from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import admin as authadmin, forms
from django.contrib.auth.models import Permission

import models


class UserCreationForm(forms.UserCreationForm):
    username = None

    class Meta:
        model = models.User
        fields = ('email',)


class UserChangeForm(forms.UserChangeForm):
    username = None

    class Meta(forms.UserChangeForm.Meta):
        model = models.User


class UserAdmin(authadmin.UserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('username', 'first_name', 'last_name')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_test_user',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )

    list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff', 'last_login')


class InternalGroupAdmin(admin.ModelAdmin):
    pass

admin.site.register(models.User, UserAdmin)
admin.site.register(models.InternalGroup, InternalGroupAdmin)
admin.site.register(Permission)
