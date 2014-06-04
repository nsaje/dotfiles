from django.contrib import admin
from django.utils.translation import ugettext, ugettext_lazy as _
from django import forms
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

import models

class CustomUserCreationForm(UserCreationForm):
    username = None

    class Meta:
        model = models.CustomUser

class CustomUserChangeForm(UserChangeForm):
    username = None 

    class Meta(UserChangeForm.Meta):
        model = models.CustomUser

class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('username', 'first_name', 'last_name')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )

    list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff')

admin.site.register(models.CustomUser, CustomUserAdmin)
