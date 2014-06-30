from django.contrib import admin
from django import forms
from django.utils.safestring import mark_safe

import constants
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
    email = forms.CharField(widget=StrWidget, label="E-mail")
    link = forms.CharField(widget=StrWidget, label="Edit link")

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
            self.fields["link"].initial = u'<a href="/admin/zemauth/user/%i">Edit user</a>' % (user.id)


class PreventEditInlineFormset(forms.BaseInlineFormSet):
    def clean(self):
        super(PreventEditInlineFormset, self).clean()

        for form in self.forms:
            pk = form.cleaned_data.get('id')
            if pk and pk.id and form.has_changed():
                raise forms.ValidationError('Editing is not allowed. Please add new entry instead.')
    # def save_existing(self, form, instance, commit=True):
    #     raise forms.ValidationError('Editing is not allowed. Please add new entry instead.')


class AdGroupSettingsForm(forms.ModelForm):
    class Meta:
        widgets = {
            'target_devices': forms.SelectMultiple(choices=constants.AdTargetDevice.get_choices()),
            'target_regions': forms.SelectMultiple(choices=constants.AdTargetCountry.get_choices())
        }


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
        'created_dt',
        'modified_dt'
    )
    readonly_fields = ('created_dt', 'modified_dt')


# Ad Group

class AdGroupNetworksInline(admin.TabularInline):
    verbose_name = "Ad Group's Network"
    verbose_name_plural = "Ad Group's Networks"
    model = models.AdGroup.networks.through
    extra = 0


class AdGroupSettingsInline(admin.TabularInline):
    verbose_name = "Ad Group's Settings"
    verbose_name_plural = "Ad Group's Settings"
    model = models.AdGroupSettings
    form = AdGroupSettingsForm
    formset = PreventEditInlineFormset
    extra = 0
    can_delete = False
    ordering = ('-created_dt',)
    readonly_fields = ('created_dt', 'created_by', 'state', 'start_date', 'end_date', 'cpc_cc', 'daily_budget_cc', 'target_devices', 'target_regions', 'tracking_code')


class AdGroupNetworkSettingsInline(admin.TabularInline):
    verbose_name = "Ad Group's Network Settings"
    verbose_name_plural = "Ad Group's Network Settings"
    model = models.AdGroupNetworkSettings
    formset = PreventEditInlineFormset
    extra = 0
    can_delete = False
    exclude = ('ad_group_network',)
    ordering = ('created_dt',)
    readonly_fields = ('created_dt', 'created_by')


class AdGroupAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = (
        'name',
        'created_dt',
        'modified_dt'
    )
    readonly_fields = ('created_dt', 'modified_dt', 'modified_by')
    inlines = (
        AdGroupSettingsInline,
        AdGroupNetworkSettingsInline,
        AdGroupNetworksInline,
    )

admin.site.register(models.Account, AccountAdmin)
admin.site.register(models.Campaign, CampaignAdmin)
admin.site.register(models.Network, NetworkAdmin)
admin.site.register(models.AdGroup, AdGroupAdmin)
