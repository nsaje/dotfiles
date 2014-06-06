from django.contrib import admin
from django import forms
from django.utils.safestring import mark_safe

import models


# Forms for inline user functionality.

class StrWidget(forms.Widget):
    def render(self, name, value, attrs=None):
        return mark_safe(unicode(value))

    def value_from_datadict(self, data, files, name):
        return "Something"


class AbstractUserForm(forms.ModelForm):
    ''' Ugly hack to bring ManyToMany related object data into a "through" object inline
    WARNING: DOES NOT SAVE THE DATA
    '''

    first_name = forms.CharField(widget=StrWidget, label="First name")
    last_name = forms.CharField(widget=StrWidget, label="Last name")
    email = forms.CharField(widget=StrWidget, label="E-mail", )
    link = forms.CharField(widget=StrWidget, label="Edit link", )

    def __init__(self, *args, **kwargs):
        super(AbstractUserForm, self).__init__(*args, **kwargs)

        if hasattr(self.instance, 'user') and self.instance.user:
            user = self.instance.user

            self.fields["first_name"].initial = user.first_name
            self.fields['first_name'].widget.attrs['disabled'] = 'disabled'
            self.fields['first_name'].required = False
            self.fields["last_name"].initial = user.last_name
            self.fields['last_name'].widget.attrs['disabled'] = 'disabled'
            self.fields['last_name'].required = False
            self.fields["email"].initial = user.email
            self.fields["link"].initial = u'<a href="/admin/auth/user/%i">Edit user</a>' % (user.id)


class PreventEditInlineForm(forms.BaseInlineFormSet):
    def clean(self):
        super(PreventEditInlineForm, self).clean()

        for form in self.forms:
            pk = form.cleaned_data.get('id')
            print form.has_changed()
            if pk and pk.id and form.has_changed():
                raise forms.ValidationError('Editing is not allowed. Please add new entry instead.')


# Account

class AccountUserInline(admin.TabularInline):
    model = models.Account.users.through
    # fields = (
    #     'get_full_name',
    # )
    form = AbstractUserForm
    extra = 0
    raw_id_fields = ("user", )

    def __unicode__(self):
        return self.name


class CampaignInline(admin.TabularInline):
    verbose_name = "Campaign"
    verbose_name_plural = "Campaigns"
    model = models.Campaign
    extra = 0
    can_delete = False
    exclude = ('users', 'created_dt', 'modified_dt', 'modified_by')
    ordering = ('-created_dt',)
    readonly_fields = ('admin_link',)


class AccountAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = (
        'name',
        'created_dt',
        'modified_dt'
    )
    readonly_fields = ('created_dt', 'modified_dt', 'modified_by')
    exclude = ('users',)
    inlines = (AccountUserInline, CampaignInline)


# Campaign

class CampaignUserInline(admin.TabularInline):
    model = models.Campaign.users.through
    extra = 0
    raw_id_fields = ("user", )

    def __unicode__(self):
        return self.name


class AdGroupInline(admin.TabularInline):
    verbose_name = "Ad Group"
    verbose_name_plural = "Ad Groups"
    model = models.AdGroup
    extra = 0
    can_delete = False
    exclude = ('users', 'created_dt', 'modified_dt', 'modified_by')
    ordering = ('-created_dt',)
    readonly_fields = ('admin_link',)


class CampaignAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = (
        'name',
        'created_dt',
        'modified_dt'
    )
    readonly_fields = ('created_dt', 'modified_dt', 'modified_by')
    exclude = ('users',)
    inlines = (CampaignUserInline, AdGroupInline)


class NetworkAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = (
        'name',
        'slug',
        'created_dt',
        'modified_dt'
    )
    readonly_fields = ('slug', 'created_dt', 'modified_dt')


# Ad Group

class AdGroupSettingsInline(admin.TabularInline):
    verbose_name = "Ad Group's Settings"
    verbose_name_plural = "Ad Group's Settings"
    model = models.AdGroupSettings
    formset = PreventEditInlineForm
    extra = 0
    can_delete = False
    ordering = ('-created_dt',)
    readonly_fields = ('created_dt', 'created_by')


class AdGroupNetworkSettingsInline(admin.TabularInline):
    verbose_name = "Ad Group's Network Settings"
    verbose_name_plural = "Ad Group's Network Settings"
    model = models.AdGroupNetworkSettings
    formset = PreventEditInlineForm
    extra = 0
    can_delete = False
    ordering = ('-created_dt',)
    readonly_fields = ('created_dt', 'created_by')


class AdGroupAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = (
        'name',
        'created_dt',
        'modified_dt'
    )
    readonly_fields = ('created_dt', 'modified_dt', 'modified_by')
    inlines = (AdGroupSettingsInline, AdGroupNetworkSettingsInline)

admin.site.register(models.Account, AccountAdmin)
admin.site.register(models.Campaign, CampaignAdmin)
admin.site.register(models.Network, NetworkAdmin)
admin.site.register(models.AdGroup, AdGroupAdmin)
