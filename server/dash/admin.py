import json
import logging
import urllib
from functools import partial

from django.contrib import admin
from django.contrib import messages
from django.db import transaction
from django import forms
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.postgres.forms import SimpleArrayField
from django.core.exceptions import ValidationError

from import_export import resources
from import_export.admin import ExportMixin

from zemauth.models import User as ZemUser

from dash import api
from dash import constants
from dash import models
from dash import forms as dash_forms
from dash import validation_helpers

import utils.k1_helper

import actionlog.api_contentads
import actionlog.zwei_actions

from automation import campaign_stop

logger = logging.getLogger(__name__)

from utils.admin_common import SaveWithRequestMixin


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


class AgencyUserForm(AbstractUserForm):
    ''' Derived from a more abstract hack with validation '''

    def __init__(self, *args, **kwargs):
        super(AgencyUserForm, self).__init__(*args, **kwargs)

    def clean(self):
        super(AgencyUserForm, self).clean()

        if 'user' not in self.cleaned_data:
            return

        agency = models.Agency.objects.filter(
            users=self.cleaned_data['user']
        ).first()
        if agency is not None and agency != self.cleaned_data.get('agency'):
            raise ValidationError('User {} is already part of another agency'.format(
                self.cleaned_data['user'].get_full_name().encode('utf-8')
            ))


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


class SourceForm(forms.ModelForm):

    def clean_default_daily_budget_cc(self):
        default_daily_budget_cc = self.cleaned_data.get('default_daily_budget_cc')
        if default_daily_budget_cc:
            validation_helpers.validate_daily_budget_cc(default_daily_budget_cc, self.cleaned_data['source_type'])

        return default_daily_budget_cc

    def clean_default_cpc_cc(self):
        cpc_cc = self.cleaned_data.get('default_cpc_cc')
        if cpc_cc:
            validation_helpers.validate_source_cpc_cc(cpc_cc, self.instance, self.cleaned_data['source_type'])

        return cpc_cc

    def clean_default_mobile_cpc_cc(self):
        cpc_cc = self.cleaned_data.get('default_mobile_cpc_cc')
        if cpc_cc:
            validation_helpers.validate_source_cpc_cc(cpc_cc, self.instance, self.cleaned_data['source_type'])

        return cpc_cc


class DefaultSourceSettingsAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = (
        'source',
        'credentials_'
    )
    readonly_fields = ('default_cpc_cc', 'mobile_cpc_cc', 'daily_budget_cc')

    def credentials_(self, obj):
        if obj.credentials is None:
            return '/'

        return '<a href="{credentials_url}">{credentials}</a>'.format(
            credentials_url=reverse('admin:dash_sourcecredentials_change', args=(obj.credentials.id,)),
            credentials=obj.credentials
        )
    credentials_.allow_tags = True
    credentials_.admin_order_field = 'credentials'


# Agency

class AgencyUserInline(admin.TabularInline):
    model = models.Agency.users.through
    form = AgencyUserForm
    extra = 0
    raw_id_fields = ("user", )
    verbose_name = "Agency Manager"
    verbose_name_plural = "Agency Managers"

    def __unicode__(self):
        return self.name


class AgencyAccountInline(admin.TabularInline):
    model = models.Account
    fk_name = 'agency'
    extra = 0
    can_delete = False

    exclude = (
        'allowed_sources',
        'outbrain_marketer_id',
        'users',
        'groups',
        'created_dt',
        'modified_dt',
        'modified_by'
    )

    ordering = ('-created_dt',)
    readonly_fields = ('admin_link',)


class AgencyFormAdmin(forms.ModelForm):
    class Meta:
        model = models.Agency
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(AgencyFormAdmin, self).__init__(*args, **kwargs)
        self.fields['sales_representative'].queryset =\
            ZemUser.objects.all().exclude(
                first_name=''
            ).exclude(
                last_name=''
            ).order_by(
                'first_name',
                'last_name',
            )
        self.fields['sales_representative'].label_from_instance = lambda obj: "%s <%s>" % (obj.get_full_name(), obj.email or '')


class AgencyAdmin(admin.ModelAdmin):
    search_fields = ['name']
    form = AgencyFormAdmin
    list_display = (
        'name',
        'id',
        '_users',
        'created_dt',
        'modified_dt',
    )
    exclude = ('users',)
    readonly_fields = ('id', 'created_dt', 'modified_dt', 'modified_by')
    inlines = (AgencyAccountInline, AgencyUserInline)

    def __init__(self, model, admin_site):
        super(AgencyAdmin, self).__init__(model, admin_site)
        self.form.admin_site = admin_site

    def _users(self, obj):
        names = []
        for user in obj.users.all():
            names.append(user.get_full_name())
        return ', '.join(names)
    _users.short_description = 'Agency Managers'

    def save_formset(self, request, form, formset, change):
        if formset.model == models.Account:
            instances = formset.save(commit=False)
            for instance in instances:
                instance.save(request)
        else:
            formset.save()

    def save_model(self, request, obj, form, change):
        obj.save(request)


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


class AccountAdmin(SaveWithRequestMixin, admin.ModelAdmin):
    search_fields = ['name']
    list_display = (
        'name',
        'created_dt',
        'modified_dt'
    )
    readonly_fields = ('created_dt', 'modified_dt', 'modified_by')
    exclude = ('users', 'groups')
    inlines = (AccountUserInline, AccountGroupInline, CampaignInline)

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
    form = dash_forms.CampaignAdminForm

    def save_model(self, request, obj, form, change):
        automatic_campaign_stop = form.cleaned_data.get('automatic_campaign_stop', None)
        new_settings = obj.get_current_settings().copy_settings()
        if new_settings.automatic_campaign_stop != automatic_campaign_stop:
            new_settings.automatic_campaign_stop = automatic_campaign_stop
            new_settings.save(request)
        obj.save(request)
        campaign_stop.perform_landing_mode_check(obj, new_settings)

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
    form = SourceForm
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
    readonly_fields = ('created_dt', 'modified_dt', 'deprecated')

    @transaction.atomic
    def deprecate_selected(self, request, queryset):
        deprecated_sources = []
        all_stopped_ad_group_sources = set()
        for source in queryset:
            if source.deprecated:
                continue
            source.deprecated = True
            source.save()
            deprecated_sources.append(source.pk)
            stopped_ad_group_sources = self._stop_ad_group_sources(source)
            all_stopped_ad_group_sources = all_stopped_ad_group_sources.union(stopped_ad_group_sources)

        if not deprecated_sources:
            self.message_user(request, "All selected sources are already deprecated.")
            return

        logger.info('SOURCE DEPRECATION: Bulk deprecation of Sources: {}'.format(deprecated_sources))
        logger.info('SOURCE DEPRECATION: Bulk deactivation of AdGroup Sources: {}'.format(all_stopped_ad_group_sources))
        self.message_user(request, "Successfully deprecated {} source(s) and deactivated {} AdGroup Source(s)."
                          .format(len(deprecated_sources), len(all_stopped_ad_group_sources)))

    deprecate_selected.short_description = "Deprecate selected sources"
    actions = [deprecate_selected]

    def _stop_ad_group_sources(self, source):
        # Deactivate all AdGroup Sources - there is no need to propagate settings updates
        stopped_ad_group_sources = set()
        settings = models.AdGroupSourceSettings.objects.filter(ad_group_source__source=source).group_current_settings()
        states = models.AdGroupSourceState.objects.filter(ad_group_source__source=source).group_current_states()
        for s in list(settings) + list(states):
            if s and s.state == constants.AdGroupSourceSettingsState.ACTIVE:
                stopped_ad_group_sources.add(s.ad_group_source_id)
                s = s.copy_settings()
                s.state = constants.AdGroupSourceSettingsState.INACTIVE
                s.save(None)
        return stopped_ad_group_sources


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
        'budgets_tz',
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


class CampaignSettingsAdmin(SaveWithRequestMixin, admin.ModelAdmin):

    def get_readonly_fields(self, request, obj=None):
        return list(set(
            [field.name for field in self.opts.local_fields] +
            [field.name for field in self.opts.local_many_to_many]
        ))

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'campaign_manager':
            kwargs['queryset'] = ZemUser.objects.all().order_by('last_name')

        return super(CampaignSettingsAdmin, self).\
            formfield_for_foreignkey(db_field, request, **kwargs)

    actions = None

    search_fields = ['campaign__name']
    list_display = (
        'campaign',
        'campaign_manager',
        'iab_category',
        'promotion_goal',
        'created_dt',
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

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


class AdGroupAdmin(SaveWithRequestMixin, admin.ModelAdmin):
    search_fields = ['name']
    list_display = (
        'name',
        'campaign_',
        'account_',
        'is_demo',
        'is_archived_',
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
reject_ad_group_sources.short_description = 'Mark selected ad group sources and their content ads as REJECTED'


class AdGroupSourceAdmin(SaveWithRequestMixin, admin.ModelAdmin):
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


class AdGroupSettingsAdmin(SaveWithRequestMixin, admin.ModelAdmin):

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
    search_fields = ['ad_group_source__ad_group__name', 'ad_group_source__source__name']
    list_display = (
        'ad_group_source',
        'state',
        'cpc_cc',
        'daily_budget_cc',
        'created_dt',
    )


class AdGroupSourceStateAdmin(admin.ModelAdmin):
    search_fields = ['ad_group_source__ad_group__name', 'ad_group_source__source__name']
    list_display = (
        'ad_group_source',
        'state',
        'cpc_cc',
        'daily_budget_cc',
        'created_dt',
    )


class UserActionLogResource(resources.ModelResource):

    class Meta:
        model = models.UserActionLog

    def _changes_text(self, settings=None):
        changes_text = '/'

        if settings:
            changes_text = settings.changes_text if settings.changes_text else '- no description -'
        return changes_text

    def _get_name(self, obj):
        return obj.name if obj else '/'

    def dehydrate_action_type(self, obj):
        return constants.UserActionType.get_text(obj.action_type)

    def dehydrate_ad_group(self, obj):
        return self._get_name(obj.ad_group)

    def dehydrate_ad_group_settings(self, obj):
        return self._changes_text(obj.ad_group_settings)

    def dehydrate_campaign(self, obj):
        return self._get_name(obj.campaign)

    def dehydrate_campaign_settings(self, obj):
        return self._changes_text(obj.campaign_settings)

    def dehydrate_account(self, obj):
        return self._get_name(obj.account)

    def dehydrate_account_settings(self, obj):
        return self._changes_text(obj.account_settings)

    def dehydrate_created_by(self, obj):
        return obj.created_by.email if obj.created_by else '/'


class UserActionLogAdmin(ExportMixin, admin.ModelAdmin):
    search_fields = ['action_type', 'created_by__email']
    list_display = (
        'created_by',
        'created_dt',
        'action_type',
        'ad_group_settings_changes_text_',
        'campaign_settings_changes_text_',
        'account_settings_changes_text_',
    )

    list_filter = ('action_type',
                   ('created_dt', admin.DateFieldListFilter),
                   ('created_by', admin.RelatedOnlyFieldListFilter))

    resource_class = UserActionLogResource

    def changelist_view(self, request, extra_context=None):
        response = super(UserActionLogAdmin, self).changelist_view(request, extra_context=extra_context)
        qs = response.context_data['cl'].queryset
        extra_context = {
            'self_managed_users': (qs.order_by('created_by').distinct('created_by')
                                   .values_list('created_by__email', flat=True))
        }

        response.context_data.update(extra_context)

        return response

    def ad_group_settings_changes_text_(self, user_action_log):
        return self._get_changes_link(
            user_action_log.ad_group,
            user_action_log.ad_group_settings,
            'admin:dash_adgroup_change',
            'admin:dash_adgroupsettings_change',
        )
    ad_group_settings_changes_text_.allow_tags = True
    ad_group_settings_changes_text_.short_description = 'Ad Group'
    ad_group_settings_changes_text_.admin_order_field = 'ad_group'

    def campaign_settings_changes_text_(self, user_action_log):
        return self._get_changes_link(
            user_action_log.campaign,
            user_action_log.campaign_settings,
            'admin:dash_campaign_change',
            'admin:dash_campaignsettings_change',
        )
    campaign_settings_changes_text_.allow_tags = True
    campaign_settings_changes_text_.short_description = 'Campaign change'
    campaign_settings_changes_text_.admin_order_field = 'campaign'

    def account_settings_changes_text_(self, user_action_log):
        return self._get_changes_link(
            user_action_log.account,
            user_action_log.account_settings,
            'admin:dash_account_change',
            None
        )
    account_settings_changes_text_.allow_tags = True
    account_settings_changes_text_.short_description = 'Account change'
    account_settings_changes_text_.admin_order_field = 'account'

    def _get_changes_link(self, obj, settings, obj_url_name, settings_url_name):
        obj_link = ''
        settings_link = ''

        if obj:
            obj_link = u'<a href="{url}">{name}</a>'.format(
                name=obj.name,
                url=reverse(obj_url_name, args=(obj.pk, )))

        if settings_url_name and settings:
            settings_link = u'<a href="{url}">{name}</a>'.format(
                name=settings.changes_text or '- no changes description -',
                url=reverse(settings_url_name, args=(settings.pk, ))
            )
        elif not settings_url_name and settings:
            settings_link = settings.changes_text or '- no changes description -'

        return u'{} / {}'.format(obj_link, settings_link)


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
        'marketer_name',
        'used',
        'created_dt',
        'modified_dt',
    )


def reject_content_ad_sources(modeladmin, request, queryset):
    logger.info(
        'BULK REJECT CONTENT AD SOURCES: Bulk reject content ad sources started. Content ad sources: {}'.format(
            [el.id for el in queryset]
        )
    )

    source = models.Source.objects.get(source_type__type=constants.SourceType.OUTBRAIN)
    ignored = []

    for content_ad_source in queryset:
        if content_ad_source.source == source:
            content_ad_source.submission_status = constants.ContentAdSubmissionStatus.REJECTED
            content_ad_source.save()
        else:
            ignored.append(content_ad_source.content_ad_id)

    if len(ignored) > 0:
        messages.warning(request, 'Marking content ad sources as rejected is only supported for the Outbrain source,\
                                   content ad sources with content ad ids {0} were ignored'.format(ignored))
reject_content_ad_sources.short_description = 'Mark selected content ad sources as REJECTED'


class ContentAdGroupSettingsStatusFilter(admin.SimpleListFilter):
    title = 'Ad group status'
    parameter_name = 'ad_group_settings_status'

    def lookups(self, request, model_admin):
        return constants.AdGroupSettingsState.get_choices()

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset

        ad_group_settingss = models.AdGroupSettings.objects.all().group_current_settings()

        queried_state = int(self.value())
        return queryset.filter(
            content_ad__ad_group_id__in=[x.ad_group_id for x in ad_group_settingss if x.state == queried_state])


class ContentAdSourceAdmin(admin.ModelAdmin):
    list_display = (
        'content_ad_id_',
        'source_content_ad_id',
        'ad_group_name',
        'ad_group_settings_status',
        'source',
        'submission_status_',
        'submission_errors',
        'created_dt',
        'modified_dt'
    )

    list_filter = ('source', 'submission_status', ContentAdGroupSettingsStatusFilter)
    actions = [reject_content_ad_sources]

    display_submission_status_colors = {
        constants.ContentAdSubmissionStatus.APPROVED: '#5cb85c',
        constants.ContentAdSubmissionStatus.REJECTED: '#d9534f',
        constants.ContentAdSubmissionStatus.PENDING: '#428bca',
        constants.ContentAdSubmissionStatus.LIMIT_REACHED: '#e6c440',
        constants.ContentAdSubmissionStatus.NOT_SUBMITTED: '#bcbcbc',
    }

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        return models.ContentAdSource.objects.filter(content_ad__ad_group__is_demo=False)

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
        return u'<a href="{account_url}">{account_name}</a> / <a href="{campaign_url}">{campaign_name}</a> / <a href="{ad_group_url}">{ad_group_name}</a> - ({ad_group_id})'.format(
            account_url=reverse('admin:dash_account_change', args=(ad_group.campaign.account.id, )),
            account_name=ad_group.campaign.account.name,
            campaign_url=reverse('admin:dash_campaign_change', args=(ad_group.campaign.id, )),
            campaign_name=ad_group.campaign.name,
            ad_group_url=reverse('admin:dash_adgroup_change', args=(ad_group.id, )),
            ad_group_name=ad_group.name,
            ad_group_id=str(ad_group.id),
        )
    ad_group_name.allow_tags = True

    def ad_group_settings_status(self, obj):
        ad_group = obj.content_ad.ad_group
        ad_group_settings = ad_group.get_current_settings()
        return constants.AdGroupSettingsState.get_text(ad_group_settings.state)

    def save_model(self, request, content_ad_source, form, change):
        current_content_ad_source = models.ContentAdSource.objects.get(id=content_ad_source.id)
        content_ad_source.save()
        utils.k1_helper.update_content_ad(content_ad_source.content_ad.ad_group_id,
                                          content_ad_source.content_ad_id)

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
        self.list_display_links = None


class CreditLineItemResource(resources.ModelResource):

    class Meta:
        model = models.CreditLineItem

    def _get_name(self, obj):
        return obj.name if obj else '/'

    def dehydrate_account(self, obj):
        return obj.account.name if obj.account else '/'

    def dehydrate_created_by(self, obj):
        return obj.created_by.email if obj.created_by else '/'

    def dehydrate_status(self, obj):
        return constants.CreditLineItemStatus.get_text(obj.status)


class CreditLineItemAdmin(ExportMixin, SaveWithRequestMixin, admin.ModelAdmin):
    list_display = (
        'account',
        'agency',
        'start_date',
        'end_date',
        'amount',
        'flat_fee_cc',
        'status',
        'license_fee',
        'created_dt',
        'created_by',
    )
    date_hierarchy = 'start_date'
    list_filter = ('status', 'license_fee', 'created_by', )
    readonly_fields = ('created_dt', 'created_by',)
    search_fields = ('account__name', 'agency__name', 'amount')
    form = dash_forms.CreditLineItemAdminForm

    resource_class = CreditLineItemResource

    def get_actions(self, request):
        actions = super(CreditLineItemAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    def has_delete_permission(self, request, obj=None):
        return False


class BudgetLineItemAdmin(SaveWithRequestMixin, admin.ModelAdmin):
    list_display = (
        '__str__',
        'campaign',
        'start_date',
        'end_date',
        'amount',
        'license_fee',
        'created_dt',
    )
    date_hierarchy = 'start_date'
    list_filter = ['credit', 'created_by']
    readonly_fields = ('created_dt', 'created_by', 'freed_cc')
    search_fields = ('campaign__name', 'campaign__account__name', 'amount')
    form = dash_forms.BudgetLineItemAdminForm


class ScheduledExportReportLogAdmin(admin.ModelAdmin):
    search_fields = ['scheduled_report']
    list_display = (
        'created_dt',
        'start_date',
        'end_date',
        'state',
        'scheduled_report',
        'recipient_emails',
        'report_filename',
        'errors'
    )
    readonly_fields = ['created_dt']


class ScheduledExportReportAdmin(admin.ModelAdmin):
    search_fields = ['name', 'created_by__email']
    list_display = (
        'created_dt',
        'created_by',
        'name',
        'report',
        'report_',
        'sending_frequency',
        'get_sources',
        'get_recipients',
        'state',
    )
    readonly_fields = ['created_dt']
    list_filter = ('state', 'sending_frequency')
    ordering = ('state', '-created_dt')

    def get_recipients(self, obj):
        return ', '.join(obj.get_recipients_emails_list())
    get_recipients.short_description = 'Recipient Emails'

    def get_sources(self, obj):
        if len(obj.report.filtered_sources.all()) == 0:
            return 'All Sources'
        return ', '.join(source.name for source in obj.report.get_filtered_sources())
    get_sources.short_description = 'Filtered Sources'

    def report_(self, obj):
        link = reverse("admin:dash_exportreport_change", args=(obj.report.id,))
        return u'<a href="%s">%s</a>' % (link, obj.report)
    report_.allow_tags = True


class ExportReportAdmin(admin.ModelAdmin):
    search_fields = ['created_by__email']
    list_display = (
        'created_dt',
        'created_by',
        'granularity',
        'breakdown_by_day',
        'breakdown_by_source',
        'order_by',
        'ad_group',
        'campaign',
        'account',
        'additional_fields',
        'get_sources'
    )
    readonly_fields = ['created_dt']

    def get_sources(self, obj):
        if len(obj.filtered_sources.all()) == 0:
            return 'All Sources'
        return ', '.join(source.name for source in obj.get_filtered_sources())
    get_sources.short_description = 'Filtered Sources'


class PublisherBlacklistAdmin(admin.ModelAdmin):
    form = dash_forms.PublisherBlacklistForm

    search_fields = ['name']
    list_display = (
        'created_dt',
        'name',
        'everywhere',
        'ad_group_',
        'campaign_',
        'account_',
        'source_id',
        'status'
    )
    readonly_fields = [
        'created_dt',
        'everywhere',
        'external_id',
        'ad_group_id',
        'campaign_id',
        'account_id',
        'status'
    ]
    list_filter = ('everywhere', 'status',)
    ordering = ('-created_dt',)

    def has_add_permission(self, request):
        return request.user.has_perm('zemauth.can_access_global_publisher_blacklist_status')

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('zemauth.can_access_global_publisher_blacklist_status')

    def ad_group_(self, obj):
        if obj.ad_group is None:
            return None
        return u'<a href="{ad_group_url}">{name}</a>'.format(
            ad_group_url=reverse('admin:dash_adgroup_change', args=(obj.ad_group.id,)),
            name=u'{} ({})'.format(
                obj.ad_group.name,
                obj.ad_group.id
            )
        )
    ad_group_.allow_tags = True
    ad_group_.admin_order_field = 'ad_group'

    def account_(self, obj):
        account = obj.account or (obj.campaign.account if obj.campaign else None)

        if account is None:
            return ""
        return '<a href="{account_url}">{account}</a>'.format(
            account_url=reverse('admin:dash_account_change', args=(account.id,)),
            account=account
        )
    account_.allow_tags = True
    account_.admin_order_field = 'campaign__account'

    def campaign_(self, obj):
        if obj.campaign is None:
            return ""
        return '<a href="{campaign_url}">{campaign}</a>'.format(
            campaign_url=reverse('admin:dash_campaign_change', args=(obj.campaign.id,)),
            campaign=obj.campaign
        )
    campaign_.allow_tags = True
    campaign_.admin_order_field = 'campaign'

    # funky hack that removes site-wide bulk model delete action
    def get_actions(self, request):
        actions = super(PublisherBlacklistAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    def get_form(self, request, obj=None, **kwargs):
        form = super(PublisherBlacklistAdmin, self).get_form(request, **kwargs)
        form.request = request
        return form

    def reenable_global(modeladmin, request, queryset):
        user = request.user
        if not user.has_perm('zemauth.can_access_global_publisher_blacklist_status'):
            return
        if not user.has_perm('zemauth.can_modify_publisher_blacklist_status'):
            return

        global_blacklist = []
        # currently only support enabling global blacklist
        filtered_queryset = queryset.filter(
            everywhere=True,
            status=constants.PublisherStatus.BLACKLISTED
        )

        # currently only support enabling global blacklist
        matching_sources = models.Source.objects.filter(
            deprecated=False
        )
        candidate_source = None
        for source in matching_sources:
            if source.can_modify_publisher_blacklist_automatically():
                candidate_source = source
                break

        for publisher_blacklist in filtered_queryset:
            global_blacklist.append({
                'domain': publisher_blacklist.name,
                'source': candidate_source,
            })

        actionlogs_to_send = []
        with transaction.atomic():
            actionlogs_to_send.extend(
                api.create_global_publisher_blacklist_actions(
                    None,
                    request,
                    constants.PublisherStatus.ENABLED,
                    global_blacklist,
                    send=False
                )
            )
        actionlog.zwei_actions.send(actionlogs_to_send)

    reenable_global.short_description = "Re-enable publishers globally"

    actions = [reenable_global]


class GAAnalyticsAccount(admin.ModelAdmin):
    pass


class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = (
        'template_type',
        'subject',
    )
    readonly_fields = ('template_type', 'subject', 'body')

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_save'] = False
        extra_context['show_save_and_add_another'] = False
        extra_context['show_save_and_continue'] = False
        return super(EmailTemplateAdmin, self).change_view(
            request, object_id,
            form_url, extra_context=extra_context
        )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return True


admin.site.register(models.Agency, AgencyAdmin)
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
admin.site.register(models.UserActionLog, UserActionLogAdmin)
admin.site.register(models.CreditLineItem, CreditLineItemAdmin)
admin.site.register(models.BudgetLineItem, BudgetLineItemAdmin)
admin.site.register(models.ScheduledExportReportLog, ScheduledExportReportLogAdmin)
admin.site.register(models.ScheduledExportReport, ScheduledExportReportAdmin)
admin.site.register(models.ExportReport, ExportReportAdmin)
admin.site.register(models.PublisherBlacklist, PublisherBlacklistAdmin)
admin.site.register(models.GAAnalyticsAccount, GAAnalyticsAccount)
admin.site.register(models.EmailTemplate, EmailTemplateAdmin)
