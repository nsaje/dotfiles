import json
import logging
import urllib

from django.contrib import admin
from django import forms
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.postgres.forms import SimpleArrayField
from django.core.exceptions import ValidationError

from zemauth.models import User as ZemUser

from dash import api
from dash import constants
from dash import models
from dash import threads

import actionlog.api_contentads
import actionlog.zwei_actions

logger = logging.getLogger(__name__)


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
            'target_regions': forms.SelectMultiple(choices=constants.AdTargetLocation.get_choices())
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
        if not instance or not instance.pk or\
           not (instance.source.source_type and instance.source.source_type.type in settings.SOURCE_OAUTH_URIS.keys()):
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
                                            reverse('dash.views.views.oauth_authorize',
                                                    kwargs={'source_name': instance.source.source_type.type}) +\
                                            '?credentials_id=' + str(instance.pk) + '">Generate tokens</a>'
        else:
            self.initial['oauth_refresh'] = 'Credentials instance contains access tokens. '\
                                            '<a href="' +\
                                            reverse('dash.views.views.oauth_authorize',
                                                    kwargs={'source_name': instance.source.source_type.type}) +\
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


class AvailableActionsField(SimpleArrayField):
    def to_python(self, value):
        return sorted([int(v) for v in value])

    def prepare_value(self, value):
        return value

    def validate(self, value):
        all_actions = set([ac[0] for ac in constants.SourceAction.get_choices()])

        errors = []
        for i, el in enumerate(value):
            if el not in all_actions:
                errors.append(ValidationError(
                    'Invalid source action',
                    code='item_invalid',
                    params={'nth': i},
                ))

        if errors:
            raise ValidationError(errors)


class SourceTypeForm(forms.ModelForm):
    available_actions = AvailableActionsField(
        forms.fields.IntegerField(),
        label='Available Actions',
        required=False,
        widget=forms.widgets.CheckboxSelectMultiple(
            choices=sorted(constants.SourceAction.get_choices(), key=lambda x: x[1])
        )
    )


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


# Account

class AccountUserInline(admin.TabularInline):
    model = models.Account.users.through
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

    def save_model(self, request, obj, form, change):
        obj.save(request)

    def save_formset(self, request, form, formset, change):
        if formset.model == models.Campaign:
            instances = formset.save(commit=False)
            for instance in instances:
                instance.save(request)

            for obj in formset.deleted_objects:
                obj.delete()
        else:
            formset.save()


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

    def save_model(self, request, obj, form, change):
        obj.save(request)

    def save_formset(self, request, form, formset, change):
        if formset.model == models.AdGroup:
            instances = formset.save(commit=False)
            for instance in instances:
                instance.save(request)

            for obj in formset.deleted_objects:
                obj.delete()
        else:
            formset.save()

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
        'source_type',
        'tracking_slug',
        'bidder_slug',
        'maintenance',
        'deprecated',
        'created_dt',
        'modified_dt',
    )
    readonly_fields = ('created_dt', 'modified_dt')


class SourceTypeAdmin(admin.ModelAdmin):
    form = SourceTypeForm

    fields = (
        'type',
        'available_actions',
        'min_cpc',
        'min_daily_budget',
        'max_cpc',
        'max_daily_budget',
        'cpc_decimal_places',
        'delete_traffic_metrics_threshold',
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('type',)
        return self.readonly_fields

    class Media:
        css = {
            'all': ('css/admin/source_type_custom.css',)
        }


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

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        obj.save(request)

# Ad Group


class AdGroupSourcesInline(admin.TabularInline):
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


class IsArchivedFilter(admin.SimpleListFilter):
    title = 'Is archived'
    parameter_name = 'is_archived'

    def lookups(self, request, model_admin):
        return (
            (1, 'Archived'),
            (0, 'Not archived'),
        )

    def queryset(self, request, queryset):
        value_bool = self.value() == '1'
        if self.value() is None:
            value_bool = False
        for obj in queryset:
            archived = False
            try:
                last_settings = obj.settings.latest('created_dt')
                archived = bool(last_settings.archived)
            except:
                pass
            if archived and not value_bool:
                queryset = queryset.exclude(id=obj.id)
            if not archived and value_bool:
                queryset = queryset.exclude(id=obj.id)
        return queryset


class AdGroupAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = (
        'name',
        'campaign_',
        'account_',
        'is_demo',
        'is_archived_',
        'content_ads_tab_with_cms_',
        'created_dt',
        'modified_dt',
        'settings_',
    )
    list_filter = [IsArchivedFilter]

    readonly_fields = ('created_dt', 'modified_dt', 'modified_by', 'settings_')
    inlines = (
        AdGroupSourcesInline,
    )

    def view_on_site(self, obj):
        return '/ad_groups/{}/ads'.format(obj.id)

    def content_ads_tab_with_cms_(self, obj):
        return obj.content_ads_tab_with_cms
    content_ads_tab_with_cms_.allow_tags = True
    content_ads_tab_with_cms_.short_description = 'Has CMS'
    content_ads_tab_with_cms_.boolean = True
    content_ads_tab_with_cms_.admin_order_field = 'content_ads_tab_with_cms'

    def is_archived_(self, obj):
        try:
            last_settings = obj.settings.latest('created_dt')
            return bool(last_settings.archived)
        except:
            pass
        return False
    is_archived_.allow_tags = True
    is_archived_.short_description = 'Is archived'
    is_archived_.boolean = True

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

    def save_model(self, request, obj, form, change):
        obj.save(request)

    def save_formset(self, request, form, formset, change):
        actions = []
        if formset.model == models.AdGroupSource:
            instances = formset.save(commit=False)

            for instance in instances:
                instance.save(request)
                for changed_instance, changed_fields in formset.changed_objects:
                    if changed_instance.id == instance.id and ('submission_status' in changed_fields or
                                                               'source_content_ad_id' in changed_fields):
                        actions.extend(api.update_content_ads_submission_status(instance))

            for obj in formset.deleted_objects:
                obj.delete()
        else:
            formset.save()

        threads.SendActionLogsThread(actions).start()


def approve_ad_group_sources(modeladmin, request, queryset):
    logger.info(
        'BULK APPROVE AD GROUP SOURCES: Bulk approve ad group sources started. Ad group sources: {}'.format(
            [el.id for el in queryset]
        )
    )
    actions = []
    for ad_group_source in queryset:
        ad_group_source.submission_status = constants.ContentAdSubmissionStatus.APPROVED
        ad_group_source.save()
        actions.extend(api.update_content_ads_submission_status(ad_group_source))
    threads.SendActionLogsThread(actions).start()
approve_ad_group_sources.short_description = 'Mark selected ad group sources and their content ads as APPROVED'


def reject_ad_group_sources(modeladmin, request, queryset):
    logger.info(
        'BULK REJECT AD GROUP SOURCES: Bulk reject ad group sources started. Ad group sources: {}'.format(
            [el.id for el in queryset]
        )
    )
    actions = []
    for ad_group_source in queryset:
        ad_group_source.submission_status = constants.ContentAdSubmissionStatus.REJECTED
        ad_group_source.save()
        actions.extend(api.update_content_ads_submission_status(ad_group_source))
    threads.SendActionLogsThread(actions).start()
reject_ad_group_sources.short_description = 'Mark selected ad group sources and their content ads as REJECTED'


class AdGroupSourceAdmin(admin.ModelAdmin):
    list_display = (
        'ad_group_',
        'source_content_ad_id',
        'submission_status_',
        'submission_errors',
    )

    actions = [approve_ad_group_sources, reject_ad_group_sources]

    list_filter = ('source', 'submission_status')

    display_submission_status_colors = {
        constants.ContentAdSubmissionStatus.APPROVED: '#5cb85c',
        constants.ContentAdSubmissionStatus.REJECTED: '#d9534f',
        constants.ContentAdSubmissionStatus.PENDING: '#428bca',
        constants.ContentAdSubmissionStatus.LIMIT_REACHED: '#e6c440',
        constants.ContentAdSubmissionStatus.NOT_SUBMITTED: '#bcbcbc',
    }

    def ad_group_(self, obj):
        return u'<a href="{ad_group_url}">{name}</a>'.format(
            ad_group_url=reverse('admin:dash_adgroup_change', args=(obj.ad_group.id,)),
            name=u'{} / {} / {} - {} ({})'.format(
                obj.ad_group.campaign.account.name,
                obj.ad_group.campaign.name,
                obj.ad_group.name,
                obj.source.name,
                obj.ad_group.id
            )
        )
    ad_group_.allow_tags = True
    ad_group_.admin_order_field = 'ad_group'

    def submission_status_(self, obj):
        return '<span style="color:{color}">{submission_status}</span>'.format(
            color=self.display_submission_status_colors[obj.submission_status],
            submission_status=obj.get_submission_status_display(),
        )
    submission_status_.allow_tags = True
    submission_status_.admin_order_field = 'submission_status'


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

    def save_model(self, request, obj, form, change):
        obj.save(request)


class AdGroupSourceSettingsAdmin(admin.ModelAdmin):
    search_fields = ['ad_group_source__ad_group__name', 'ad_group_source__source__name']
    list_display = (
        'ad_group_source',
        'state',
        'cpc_cc',
        'daily_budget_cc',
        'created_dt',
    )

    def save_model(self, request, obj, form, change):
        obj.save(request)


class AdGroupSourceStateAdmin(admin.ModelAdmin):
    search_fields = ['ad_group_source__ad_group__name', 'ad_group_source__source__name']
    list_display = (
        'ad_group_source',
        'state',
        'cpc_cc',
        'daily_budget_cc',
        'created_dt',
    )


class AdGroupModelChoiceField(forms.ModelChoiceField):

    def label_from_instance(self, obj):
        return u'{} | {} | {}'.format(obj.campaign.account.name, obj.campaign.name, obj.name)


class DemoAdGroupRealAdGroupAdminForm(forms.ModelForm):

    demo_ad_group = AdGroupModelChoiceField(
        queryset=models.AdGroup.objects.order_by('campaign__account__name')
    )
    real_ad_group = AdGroupModelChoiceField(
        queryset=models.AdGroup.objects.order_by('campaign__account__name')
    )

    def clean_demo_ad_group(self):
        if not self.cleaned_data['demo_ad_group'].is_demo:
            raise forms.ValidationError('Only adgroups which have is_demo set to True can be chosen as demo ad groups')
        return self.cleaned_data['demo_ad_group']

    def clean_real_ad_group(self):
        if self.cleaned_data['real_ad_group'].is_demo:
            raise forms.ValidationError('Cannot choose an adgroup with is_demo set to True as a real ad group')
        return self.cleaned_data['real_ad_group']


class DemoAdGroupRealAdGroupAdmin(admin.ModelAdmin):
    list_display = (
        'demo_ad_group_',
        'real_ad_group_',
        'multiplication_factor'
    )
    form = DemoAdGroupRealAdGroupAdminForm

    def demo_ad_group_(self, obj):
        ad_group_name = obj.demo_ad_group.name
        campaign_name = obj.demo_ad_group.campaign.name
        account_name = obj.demo_ad_group.campaign.account.name
        return u'|'.join([account_name, campaign_name, ad_group_name])

    def real_ad_group_(self, obj):
        ad_group_name = obj.real_ad_group.name
        campaign_name = obj.real_ad_group.campaign.name
        account_name = obj.real_ad_group.campaign.account.name
        return u'|'.join([account_name, campaign_name, ad_group_name])


class OutbrainAccountAdmin(admin.ModelAdmin):
    list_display = (
        'marketer_id',
        'used',
        'created_dt',
        'modified_dt',
    )


class ContentAdSourceAdmin(admin.ModelAdmin):
    list_display = (
        'content_ad_id_',
        'source_content_ad_id',
        'ad_group_name',
        'source',
        'submission_status_',
        'submission_errors',
        'created_dt',
        'modified_dt'
    )

    list_filter = ('source', 'submission_status')

    display_submission_status_colors = {
        constants.ContentAdSubmissionStatus.APPROVED: '#5cb85c',
        constants.ContentAdSubmissionStatus.REJECTED: '#d9534f',
        constants.ContentAdSubmissionStatus.PENDING: '#428bca',
        constants.ContentAdSubmissionStatus.LIMIT_REACHED: '#e6c440',
        constants.ContentAdSubmissionStatus.NOT_SUBMITTED: '#bcbcbc',
    }

    def submission_status_(self, obj):
        return '<span style="color:{color}">{submission_status}</span>'.format(
            color=self.display_submission_status_colors[obj.submission_status],
            submission_status=obj.get_submission_status_display(),
        )
    submission_status_.allow_tags = True
    submission_status_.admin_order_field = 'submission_status'

    def content_ad_id_(self, obj):
        return obj.content_ad.id
    content_ad_id_.admin_order_field = 'content_ad_id'

    def ad_group_name(self, obj):
        ad_group = obj.content_ad.ad_group
        return ad_group.campaign.account.name + ' / ' + ad_group.campaign.name + ' / ' + ad_group.name + ' (' + str(ad_group.id) + ')'

    def save_model(self, request, content_ad_source, form, change):
        current_content_ad_source = models.ContentAdSource.objects.get(id=content_ad_source.id)
        content_ad_source.save()

        if current_content_ad_source.submission_status != content_ad_source.submission_status and\
           content_ad_source.submission_status == constants.ContentAdSubmissionStatus.APPROVED:
            changes = {
                'state': content_ad_source.state,
            }

            actionlog.api_contentads.init_update_content_ad_action(
                content_ad_source,
                changes,
                request
            )

    def __init__(self, *args, **kwargs):
        super(ContentAdSourceAdmin, self).__init__(*args, **kwargs)
        self.list_display_links = (None, )


admin.site.register(models.Account, AccountAdmin)
admin.site.register(models.Campaign, CampaignAdmin)
admin.site.register(models.CampaignSettings, CampaignSettingsAdmin)
admin.site.register(models.Source, SourceAdmin)
admin.site.register(models.AdGroup, AdGroupAdmin)
admin.site.register(models.AdGroupSource, AdGroupSourceAdmin)
admin.site.register(models.AdGroupSettings, AdGroupSettingsAdmin)
admin.site.register(models.AdGroupSourceSettings, AdGroupSourceSettingsAdmin)
admin.site.register(models.AdGroupSourceState, AdGroupSourceStateAdmin)
admin.site.register(models.SourceCredentials, SourceCredentialsAdmin)
admin.site.register(models.SourceType, SourceTypeAdmin)
admin.site.register(models.DefaultSourceSettings, DefaultSourceSettingsAdmin)
admin.site.register(models.DemoAdGroupRealAdGroup, DemoAdGroupRealAdGroupAdmin)
admin.site.register(models.OutbrainAccount, OutbrainAccountAdmin)
admin.site.register(models.ContentAdSource, ContentAdSourceAdmin)
