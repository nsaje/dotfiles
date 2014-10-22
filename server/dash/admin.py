import urllib

from django.contrib import admin
from django import forms
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from django.conf import settings

from zemauth.models import User as ZemUser

import constants
import models
import json


# Forms for inline user functionality.

class StrWidget(forms.Widget):
    def render(self, name, value, attrs=None):
        return mark_safe(unicode(value))

    def value_from_datadict(self, data, files, name):
        return "Something"


class StrFieldWidget(forms.Widget):
    def render(self, name, value, attrs=None):
        return mark_safe('<p>' + unicode(value) + '</p>')

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
            self.fields["link"].initial = u'<a href="/admin/zemauth/user/%i/">Edit user</a>' % (user.id)


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


# Always empty form for source credentials and a link for refresing OAuth credentials for
# sources that use them

class SourceCredentialsForm(forms.ModelForm):
    credentials = forms.CharField(
        label='Credentials',
        required=False,
        widget=forms.Textarea(
            attrs={'rows': 15, 'cols': 60})
    )
    oauth_refresh = forms.CharField(label='OAuth tokens', required=False, widget=StrFieldWidget)

    def _set_oauth_refresh(self, instance):
        if not instance or not instance.pk or instance.source.type not in settings.SOURCE_OAUTH_URIS.keys():
            self.fields['oauth_refresh'].widget = forms.HiddenInput()
            return

        self.initial['oauth_refresh'] = ''
        self.fields['oauth_refresh'].widget.attrs['readonly'] = True

        decrypted = instance.decrypt()
        if 'client_id' not in decrypted or 'client_secret' not in decrypted:
            self.initial['oauth_refresh'] = 'Credentials instance doesn\'t contain client_id or client_secret. '\
                                            'Unable to refresh OAuth tokens.'
            return

        if 'oauth_tokens' not in decrypted:
            self.initial['oauth_refresh'] = 'Credentials instance doesn\'t contain access tokens. '\
                                            '<a href="' +\
                                            reverse('dash.views.oauth_authorize',
                                                    kwargs={'source_name': instance.source.type}) +\
                                            '?credentials_id=' + str(instance.pk) + '">Generate tokens</a>'
        else:
            self.initial['oauth_refresh'] = 'Credentials instance contains access tokens. '\
                                            '<a href="' +\
                                            reverse('dash.views.oauth_authorize',
                                                    kwargs={'source_name': instance.source.type}) +\
                                            '?credentials_id=' + str(instance.pk) + '">Refresh tokens</a>'

    def __init__(self, *args, **kwargs):
        super(SourceCredentialsForm, self).__init__(*args, **kwargs)
        self._set_oauth_refresh(kwargs.get('instance'))
        self.initial['credentials'] = ''
        self.fields['credentials'].help_text = \
            'The value in this field is automatically encrypted upon saving '\
            'for security purposes and is hidden from the interface. The '\
            'value can be changed and has to be in valid JSON format. '\
            'Leaving the field empty won\'t change the stored value.'

    def clean_credentials(self):
        if self.cleaned_data['credentials'] != '' or not self.instance.id:
            try:
                json.loads(self.cleaned_data['credentials'])
            except ValueError:
                raise forms.ValidationError('JSON format expected.')
        return self.cleaned_data['credentials']

    def clean(self, *args, **kwargs):
        super(SourceCredentialsForm, self).clean(*args, **kwargs)
        if 'credentials' in self.cleaned_data and self.cleaned_data['credentials'] == '':
            del self.cleaned_data['credentials']


class DefaultSourceSettingsAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = (
        'source',
        'credentials_'
    )

    def credentials_(self, obj):
        if obj.credentials is None:
            return '/'

        return '<a href="{credentials_url}">{credentials}</a>'.format(
            credentials_url=reverse('admin:dash_sourcecredentials_change', args=(obj.credentials.id,)),
            credentials=obj.credentials
        )
    credentials_.allow_tags = True
    credentials_.admin_order_field = 'credentials'


class AdGroupSourceForm(forms.ModelForm):

    def clean(self):

        # This is a hack to bypass a bug in django-jsonfield which doesn't
        # handle unique constraints on models very well. The unique field
        # in this case should actually be removed, but the current Django
        # version we are using (1.7 RC1) has a bug that crashes the
        # application when trying to remove the unique constraints.
        #
        # When a more stable version of Django is used, this should be
        # removed, along with the unique constraint in the models on
        # source_id and source_campaign_key
        if 'source_campaign_key' in self.cleaned_data:
            self.cleaned_data['source_campaign_key'] = json.dumps(self.cleaned_data['source_campaign_key'])

        return self.cleaned_data


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


class AccountGroupInline(admin.TabularInline):
    model = models.Account.groups.through
    extra = 0


class CampaignInline(admin.TabularInline):
    verbose_name = "Campaign"
    verbose_name_plural = "Campaigns"
    model = models.Campaign
    extra = 0
    can_delete = False
    exclude = ('users', 'groups', 'created_dt', 'modified_dt', 'modified_by')
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
    exclude = ('users', 'groups')
    inlines = (AccountUserInline, AccountGroupInline, CampaignInline)


# Campaign

class CampaignUserInline(admin.TabularInline):
    model = models.Campaign.users.through
    extra = 0
    raw_id_fields = ("user", )

    def __unicode__(self):
        return self.name


class CampaignGroupInline(admin.TabularInline):
    model = models.Campaign.groups.through
    extra = 0


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
        'modified_dt',
        'settings_'
    )
    readonly_fields = ('created_dt', 'modified_dt', 'modified_by', 'settings_')
    exclude = ('users', 'groups')
    inlines = (CampaignUserInline, CampaignGroupInline, AdGroupInline)

    def settings_(self, obj):
        return '<a href="{admin_url}">List ({num_settings})</a>'.format(
            admin_url='{}?{}'.format(
                reverse('admin:dash_campaignsettings_changelist'),
                urllib.urlencode({'campaign': obj.id})
            ),
            num_settings=obj.settings.count()
        )
    settings_.allow_tags = True

    def view_on_site(self, obj):
        return '/campaigns/{}/agency'.format(obj.id)


class SourceAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = (
        'name',
        'maintenance',
        'created_dt',
        'modified_dt',
    )
    readonly_fields = ('created_dt', 'modified_dt')


class SourceCredentialsAdmin(admin.ModelAdmin):
    form = SourceCredentialsForm
    verbose_name = "Source Credentials"
    verbose_name_plural = "Source Credentials"
    search_fields = ['name', 'source']
    list_display = (
        'name',
        'source',
        'created_dt',
        'modified_dt',
    )
    readonly_fields = ('created_dt', 'modified_dt')


class CampaignSettingsAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        return list(set(
            [field.name for field in self.opts.local_fields] +
            [field.name for field in self.opts.local_many_to_many]
        ))

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'account_manager':
            kwargs['queryset'] = ZemUser.objects.get_users_with_perm(
                'campaign_settings_account_manager'
            ).order_by('last_name')
        elif db_field.name == 'sales_representative':
            kwargs['queryset'] = ZemUser.objects.get_users_with_perm(
                'campaign_settings_sales_rep'
            ).order_by('last_name')

        return super(CampaignSettingsAdmin, self).\
            formfield_for_foreignkey(db_field, request, **kwargs)

    actions = None

    search_fields = ['campaign__name']
    list_display = (
        'campaign',
        'account_manager',
        'sales_representative',
        'service_fee',
        'iab_category',
        'promotion_goal',
        'created_dt',
    )

    def has_delete_permission(self, request, obj=None):
        return False

# Ad Group


class AdGroupSourcesInline(admin.TabularInline):
    form = AdGroupSourceForm
    verbose_name = "Ad Group's Source"
    verbose_name_plural = "Ad Group's Sources"
    model = models.AdGroupSource
    extra = 0
    readonly_fields = ('settings_',)

    def settings_(self, obj):
        return '<a href="{admin_url}">List ({num_settings})</a>'.format(
            admin_url='{}?{}'.format(
                reverse('admin:dash_adgroupsourcesettings_changelist'),
                urllib.urlencode({
                    'ad_group_source': obj.id,
                })
            ),
            num_settings=obj.settings.count()
        )
    settings_.allow_tags = True


class AdGroupAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = (
        'name',
        'campaign_',
        'account_',
        'created_dt',
        'modified_dt',
        'settings_',
    )
    readonly_fields = ('created_dt', 'modified_dt', 'modified_by', 'settings_')
    inlines = (
        AdGroupSourcesInline,
    )

    def view_on_site(self, obj):
        return '/ad_groups/{}/ads'.format(obj.id)

    def settings_(self, obj):
        return '<a href="{admin_url}">List ({num_settings})</a>'.format(
            admin_url='{}?{}'.format(
                reverse('admin:dash_adgroupsettings_changelist'),
                urllib.urlencode({'ad_group': obj.id})
            ),
            num_settings=obj.settings.count()
        )
    settings_.allow_tags = True

    def account_(self, obj):
        return '<a href="{account_url}">{account}</a>'.format(
            account_url=reverse('admin:dash_account_change', args=(obj.campaign.account.id,)),
            account=obj.campaign.account
        )
    account_.allow_tags = True
    account_.admin_order_field = 'campaign__account'

    def campaign_(self, obj):
        return '<a href="{campaign_url}">{campaign}</a>'.format(
            campaign_url=reverse('admin:dash_campaign_change', args=(obj.campaign.id,)),
            campaign=obj.campaign
        )
    campaign_.allow_tags = True
    campaign_.admin_order_field = 'campaign'


class AdGroupSettingsAdmin(admin.ModelAdmin):

    actions = None

    search_fields = ['ad_group__name']
    list_display = (
        'ad_group',
        'state',
        'cpc_cc',
        'daily_budget_cc',
        'start_date',
        'end_date',
        'created_dt',
    )

    def has_delete_permission(self, request, obj=None):
        return False


class AdGroupSourceSettingsAdmin(admin.ModelAdmin):
    search_fields = ['ad_group']
    list_display = (
        'ad_group_source',
        'state',
        'cpc_cc',
        'daily_budget_cc',
        'created_dt',
    )


class DemoAdGroupRealAdGroupAdmin(admin.ModelAdmin):
    list_display = (
        'demo_ad_group',
        'real_ad_group',
        'multiplication_factor'
    )


admin.site.register(models.Account, AccountAdmin)
admin.site.register(models.Campaign, CampaignAdmin)
admin.site.register(models.CampaignSettings, CampaignSettingsAdmin)
admin.site.register(models.Source, SourceAdmin)
admin.site.register(models.AdGroup, AdGroupAdmin)
admin.site.register(models.AdGroupSettings, AdGroupSettingsAdmin)
admin.site.register(models.AdGroupSourceSettings, AdGroupSourceSettingsAdmin)
admin.site.register(models.SourceCredentials, SourceCredentialsAdmin)
admin.site.register(models.DefaultSourceSettings, DefaultSourceSettingsAdmin)
admin.site.register(models.DemoAdGroupRealAdGroup, DemoAdGroupRealAdGroupAdmin)
