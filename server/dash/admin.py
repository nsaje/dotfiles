import datetime
import json

import tagulous.admin
from django import forms
from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.contrib import messages
from django.contrib.admin import SimpleListFilter
from django.contrib.postgres.forms import SimpleArrayField
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from import_export import fields
from import_export import resources
from import_export.admin import ExportMixin

import core.features.source_adoption
import utils.email_helper
import utils.exc
import utils.k1_helper
import utils.slack
from automation import campaignstop
from core.models import tags
from core.models.settings.ad_group_source_settings import validation_helpers
from dash import constants
from dash import cpc_constraints
from dash import forms as dash_forms
from dash import models
from dash.features.custom_flags.slack_logger import SlackLoggerMixin
from dash.features.submission_filters.admin import SubmissionFilterAdmin
from utils import zlogging
from utils.admin_common import SaveWithRequestMixin
from zemauth.models import User as ZemUser

logger = zlogging.getLogger(__name__)


# Forms for inline user functionality.
class StrWidget(forms.Widget):
    def render(self, name, value, attrs=None, renderer=None):
        return mark_safe(str(value))

    def value_from_datadict(self, data, files, name):
        return "Something"


class StrFieldWidget(forms.Widget):
    def render(self, name, value, attrs=None, renderer=None):
        return mark_safe("<p>" + str(value) + "</p>")

    def value_from_datadict(self, data, files, name):
        return "Something"


class AbstractUserForm(forms.ModelForm):
    """ Ugly hack to bring ManyToMany related object data into a "through" object inline
    WARNING: DOES NOT SAVE THE DATA
    """

    first_name = dash_forms.PlainCharField(widget=StrWidget, label="First name")
    last_name = dash_forms.PlainCharField(widget=StrWidget, label="Last name")
    email = dash_forms.PlainCharField(widget=StrWidget, label="E-mail")
    link = dash_forms.PlainCharField(widget=StrWidget, label="Edit link")

    def __init__(self, *args, **kwargs):
        super(AbstractUserForm, self).__init__(*args, **kwargs)

        if hasattr(self.instance, "user") and self.instance.user:
            user = self.instance.user

            self.fields["first_name"].initial = user.first_name
            self.fields["first_name"].widget.attrs["disabled"] = "disabled"
            self.fields["first_name"].required = False
            self.fields["last_name"].initial = user.last_name
            self.fields["last_name"].widget.attrs["disabled"] = "disabled"
            self.fields["last_name"].required = False
            self.fields["link"].initial = '<a href="/admin/zemauth/user/%i/">Edit user</a>' % (user.id)


class AgencyUserForm(AbstractUserForm):
    """ Derived from a more abstract hack with validation """

    def __init__(self, *args, **kwargs):
        super(AgencyUserForm, self).__init__(*args, **kwargs)


class PreventEditInlineFormset(forms.BaseInlineFormSet):
    def clean(self):
        super(PreventEditInlineFormset, self).clean()

        for form in self.forms:
            pk = form.cleaned_data.get("id")
            if pk and pk.id and form.has_changed():
                raise forms.ValidationError("Editing is not allowed. Please add new entry instead.")

    # def save_existing(self, form, instance, commit=True):
    #     raise forms.ValidationError('Editing is not allowed. Please add new entry instead.')


class AdGroupSettingsForm(forms.ModelForm):
    class Meta:
        widgets = {
            "target_devices": forms.SelectMultiple(choices=constants.AdTargetDevice.get_choices()),
            "target_regions": forms.SelectMultiple(choices=constants.AdTargetLocation.get_choices()),
        }


class DirectDealConnectionAgencyInline(admin.StackedInline):
    model = models.DirectDealConnection
    can_delete = True
    extra = 0
    autocomplete_fields = ("deal",)
    exclude = ("created_dt", "modified_dt", "adgroup", "campaign", "account")
    readonly_fields = ("created_by", "modified_by")
    raw_id_fields = ("agency_id",)


class DirectDealConnectionAccountInline(admin.StackedInline):
    model = models.DirectDealConnection
    can_delete = True
    extra = 0
    autocomplete_fields = ("deal",)
    exclude = ("created_dt", "modified_dt", "adgroup", "campaign", "agency")
    readonly_fields = ("created_by", "modified_by")
    raw_id_fields = ("account_id",)


class DirectDealConnectionCampaignInline(admin.StackedInline):
    model = models.DirectDealConnection
    can_delete = True
    extra = 0
    autocomplete_fields = ("deal",)
    exclude = ("created_dt", "modified_dt", "adgroup", "account", "agency")
    readonly_fields = ("created_by", "modified_by")
    raw_id_fields = ("campaign_id",)


class DirectDealConnectionAdGroupsInline(admin.StackedInline):
    model = models.DirectDealConnection
    can_delete = True
    extra = 0
    autocomplete_fields = ("deal",)
    exclude = ("created_dt", "modified_dt", "agency", "account", "campaign")
    readonly_fields = ("created_by", "modified_by")
    raw_id_fields = ("adgroup_id",)


# Always empty form for source credentials and a link for refresing OAuth credentials for sources that use them
class SourceCredentialsForm(forms.ModelForm):
    credentials = forms.CharField(
        label="Credentials", required=False, widget=forms.Textarea(attrs={"rows": 15, "cols": 60})
    )
    oauth_refresh = forms.CharField(label="OAuth tokens", required=False, widget=StrFieldWidget)

    def _set_oauth_refresh(self, instance):
        if (
            not instance
            or not instance.pk
            or not (
                instance.source.source_type
                and instance.source.source_type.type in list(settings.SOURCE_OAUTH_URIS.keys())
            )
        ):
            self.fields["oauth_refresh"].widget = forms.HiddenInput()
            return

        self.initial["oauth_refresh"] = ""
        self.fields["oauth_refresh"].widget.attrs["readonly"] = True

        decrypted = instance.decrypt()
        if "client_id" not in decrypted or "client_secret" not in decrypted:
            self.initial["oauth_refresh"] = (
                "Credentials instance doesn't contain client_id or client_secret. " "Unable to refresh OAuth tokens."
            )
            return

        if "oauth_tokens" not in decrypted:
            self.initial["oauth_refresh"] = (
                "Credentials instance doesn't contain access tokens. "
                '<a href="'
                + reverse("dash.views.views.oauth_authorize", kwargs={"source_name": instance.source.source_type.type})
                + "?credentials_id="
                + str(instance.pk)
                + '">Generate tokens</a>'
            )
        else:
            self.initial["oauth_refresh"] = (
                "Credentials instance contains access tokens. "
                '<a href="'
                + reverse("dash.views.views.oauth_authorize", kwargs={"source_name": instance.source.source_type.type})
                + "?credentials_id="
                + str(instance.pk)
                + '">Refresh tokens</a>'
            )

    def __init__(self, *args, **kwargs):
        super(SourceCredentialsForm, self).__init__(*args, **kwargs)
        self._set_oauth_refresh(kwargs.get("instance"))
        self.initial["credentials"] = ""
        self.fields["credentials"].help_text = (
            "The value in this field is automatically encrypted upon saving "
            "for security purposes and is hidden from the interface. The "
            "value can be changed and has to be in valid JSON format. "
            "Leaving the field empty won't change the stored value."
        )

    def clean_credentials(self):
        if self.cleaned_data["credentials"] != "" or not self.instance.id:
            try:
                json.loads(self.cleaned_data["credentials"])
            except ValueError:
                raise forms.ValidationError("JSON format expected.")
        return self.cleaned_data["credentials"]

    def clean(self, *args, **kwargs):
        super(SourceCredentialsForm, self).clean(*args, **kwargs)
        if "credentials" in self.cleaned_data and self.cleaned_data["credentials"] == "":
            del self.cleaned_data["credentials"]


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
                errors.append(ValidationError("Invalid source action", code="item_invalid", params={"nth": i}))

        if errors:
            raise ValidationError(errors)


class SourceTypeForm(forms.ModelForm):
    available_actions = AvailableActionsField(
        forms.fields.IntegerField(),
        label="Available Actions",
        required=False,
        widget=forms.widgets.CheckboxSelectMultiple(
            choices=sorted(constants.SourceAction.get_choices(), key=lambda x: x[1])
        ),
    )


class SourceForm(forms.ModelForm):
    def clean_default_daily_budget_cc(self):
        default_daily_budget_cc = self.cleaned_data.get("default_daily_budget_cc")
        if default_daily_budget_cc:
            validation_helpers.validate_daily_budget_cc(default_daily_budget_cc, self.cleaned_data["source_type"])

        return default_daily_budget_cc

    def clean_default_cpc_cc(self):
        cpc_cc = self.cleaned_data.get("default_cpc_cc")
        if cpc_cc:
            validation_helpers.validate_source_cpc_cc(cpc_cc, self.instance, self.cleaned_data["source_type"])

        return cpc_cc

    def clean_default_mobile_cpc_cc(self):
        cpc_cc = self.cleaned_data.get("default_mobile_cpc_cc")
        if cpc_cc:
            validation_helpers.validate_source_cpc_cc(cpc_cc, self.instance, self.cleaned_data["source_type"])

        return cpc_cc

    def clean_default_cpm(self):
        cpm = self.cleaned_data.get("default_cpm")
        if cpm:
            validation_helpers.validate_source_cpm(cpm, self.instance, self.cleaned_data["source_type"])

        return cpm

    def clean_default_mobile_cpm(self):
        cpm = self.cleaned_data.get("default_mobile_cpm")
        if cpm:
            validation_helpers.validate_source_cpm(cpm, self.instance, self.cleaned_data["source_type"])

        return cpm


# Default Sources Settings
class DefaultSourceSettingsAdmin(admin.ModelAdmin):
    search_fields = ("source__name",)
    list_display = ("source", "credentials_")
    readonly_fields = ("default_cpc_cc", "mobile_cpc_cc", "daily_budget_cc")
    autocomplete_fields = ("source", "credentials")

    def get_queryset(self, request):
        qs = super(DefaultSourceSettingsAdmin, self).get_queryset(request)
        qs = qs.select_related("credentials", "source")
        return qs

    def credentials_(self, obj):
        if obj.credentials is None:
            return "/"

        return mark_safe(
            '<a href="{credentials_url}">{credentials}</a>'.format(
                credentials_url=reverse("admin:dash_sourcecredentials_change", args=(obj.credentials.id,)),
                credentials=obj.credentials,
            )
        )

    credentials_.admin_order_field = "credentials"


class AgencyResource(resources.ModelResource):
    agency_managers = fields.Field(column_name="agency_managers")
    accounts = fields.Field(column_name="accounts")

    class Meta:
        model = models.Agency
        fields = ["id", "name", "accounts", "sales_representative", "cs_representative", "default_account_type"]
        export_order = ["id", "name", "accounts", "sales_representative", "cs_representative", "default_account_type"]

    def dehydrate_sales_representative(self, obj):
        return obj.sales_representative and obj.sales_representative.get_full_name() or ""

    def dehydrate_cs_representative(self, obj):
        return obj.cs_representative and obj.cs_representative.get_full_name() or ""

    def dehydrate_accounts(self, obj):
        return ", ".join([str(account) for account in obj.account_set.all()])

    def dehydrate_default_account_type(self, obj):
        return constants.AccountType.get_text(obj.default_account_type)


class AgencyAdmin(SlackLoggerMixin, ExportMixin, admin.ModelAdmin):
    form = dash_forms.AgencyAdminForm
    list_display = (
        "name",
        "id",
        "_accounts",
        "sales_representative",
        "cs_representative",
        "default_account_type",
        "created_dt",
        "modified_dt",
    )
    raw_id_fields = ("default_whitelist", "default_blacklist")
    readonly_fields = (
        "id",
        "created_dt",
        "modified_dt",
        "modified_by",
        "settings",
        "_accounts_cs",
        "custom_attributes",
    )
    inlines = (DirectDealConnectionAgencyInline,)
    resource_class = AgencyResource
    search_fields = ("name", "id")
    autocomplete_fields = ("available_sources", "allowed_sources", "ob_sales_representative", "ob_account_manager")

    def __init__(self, model, admin_site):
        super(AgencyAdmin, self).__init__(model, admin_site)
        self.form.admin_site = admin_site

    def get_form(self, request, obj=None, **kwargs):
        form = super(AgencyAdmin, self).get_form(request, obj=obj, **kwargs)
        form.request = request
        return form

    def get_queryset(self, request):
        qs = super(AgencyAdmin, self).get_queryset(request)
        return qs.select_related(
            "sales_representative", "ob_sales_representative", "ob_account_manager", "cs_representative"
        ).prefetch_related("account_set")

    def _accounts(self, obj):
        return ", ".join([str(account) for account in obj.account_set.all()])

    def _accounts_cs(self, obj):
        return ", ".join(
            [
                "{} {}".format(
                    account.name,
                    "({})".format(account.settings.default_cs_representative)
                    if account.settings.default_cs_representative
                    else "",
                )
                for account in obj.account_set.all()
            ]
        )

    _accounts.short_description = "Accounts"

    def save_model(self, request, obj, form, change):
        self._update_model(request, obj, form, change) if obj.id else obj.save(request)

    def _update_model(self, request, obj, form, change):
        old_obj = models.Agency.objects.get(id=obj.id)
        fields_to_update = {
            k: v for k, v in form.cleaned_data.items() if k in old_obj._update_fields and v != getattr(old_obj, k)
        }
        old_obj.update(request, **fields_to_update)
        self._handle_history(request, obj, fields_to_update)
        settings_to_update = {
            k: v
            for k, v in form.cleaned_data.items()
            if k in old_obj.settings._settings_fields and v != getattr(old_obj.settings, k)
        }
        old_obj.settings.update(request, **settings_to_update)

        utils.k1_helper.update_ad_groups(
            models.AdGroup.objects.filter(campaign__account__agency_id=obj.id)
            .select_related("campaign")
            .only("id", "campaign__account_id"),
            "AgencyAdmin.save_model",
        )

        self.log_custom_flags_event_to_slack(old_obj, obj, user=request.user.email)

    def _handle_history(self, request, agency, changes):
        if "is_disabled" in changes:
            agency.write_history(
                "Account {}.".format("disabled" if changes["is_disabled"] else "enabled"), user=request.user
            )

    def render_change_form(self, request, context, *args, **kwargs):
        context["adminform"].form.fields["sales_representative"].queryset = ZemUser.objects.get_users_with_perm(
            "campaign_settings_sales_rep"
        ).filter(is_active=True)
        context["adminform"].form.fields["cs_representative"].queryset = ZemUser.objects.get_users_with_perm(
            "campaign_settings_cs_rep"
        ).filter(is_active=True)
        return super(AgencyAdmin, self).render_change_form(request, context, args, kwargs)


class AccountAdmin(SlackLoggerMixin, SaveWithRequestMixin, admin.ModelAdmin):
    form = dash_forms.AccountAdminForm
    search_fields = ("name", "id")
    list_display = ("id", "name", "amplify_account_name", "created_dt", "modified_dt", "salesforce_url")
    readonly_fields = (
        "name",
        "amplify_account_name",
        "salesforce_url",
        "currency",
        "allowed_sources",
        "created_dt",
        "modified_dt",
        "modified_by",
        "id",
        "outbrain_marketer_id",
        "default_whitelist",
        "default_blacklist",
        "agency",
        "settings",
        "salesforce_id",
        "custom_attributes",
        "is_externally_managed",
        "amplify_account_name",
    )
    exclude = ("settings",)
    filter_horizontal = ("allowed_sources",)
    inlines = (DirectDealConnectionAccountInline,)

    def get_form(self, request, obj=None, **kwargs):
        form = super(AccountAdmin, self).get_form(request, obj=obj, **kwargs)
        form.request = request
        return form

    def save_formset(self, request, form, formset, change):
        if formset.model == models.Campaign:
            instances = formset.save(commit=False)
            for instance in instances:
                instance.update(request, **form.cleaned_data)

            for obj in formset.deleted_objects:
                obj.delete()
        else:
            formset.save()

    def save_model(self, request, obj, form, change):
        old_obj = models.Account.objects.get(id=obj.id)
        fields_to_update = {
            k: v for k, v in form.cleaned_data.items() if k in old_obj._update_fields and v != getattr(old_obj, k)
        }
        old_obj.update(request, **fields_to_update)
        self._handle_history(request, obj, fields_to_update)
        utils.k1_helper.update_ad_groups(
            models.AdGroup.objects.filter(campaign__account_id=obj.id)
            .select_related("campaign")
            .only("id", "campaign__account_id"),
            "AccountAdmin.save_model",
        )
        self.log_custom_flags_event_to_slack(old_obj, obj, user=request.user.email)

    def _handle_history(self, request, account, changes):
        if "is_disabled" in changes:
            account.write_history(
                "Account {}.".format("disabled" if changes["is_disabled"] else "enabled"), user=request.user
            )

    def view_on_site(self, obj):
        return "/v2/analytics/account/{}?settings".format(obj.id)

    def amplify_account_name(self, obj):
        if not obj.outbrain_marketer_id:
            return ""
        return models.OutbrainAccount.objects.get(marketer_id=obj.outbrain_marketer_id).marketer_name

    amplify_account_name.description = "Amplify account name"


class CampaignAdmin(SlackLoggerMixin, admin.ModelAdmin):
    search_fields = ("name", "id")
    list_display = ("id", "name", "created_dt", "modified_dt")
    readonly_fields = (
        "archived",
        "name",
        "type",
        "created_dt",
        "modified_dt",
        "modified_by",
        "id",
        "account",
        "default_whitelist",
        "default_blacklist",
    )
    raw_id_fields = ("default_whitelist", "default_blacklist")
    exclude = ("settings",)
    inlines = (DirectDealConnectionCampaignInline,)
    form = dash_forms.CampaignAdminForm

    def get_form(self, request, obj=None, **kwargs):
        form = super(CampaignAdmin, self).get_form(request, obj=obj, **kwargs)
        form.request = request
        return form

    def save_model(self, request, obj, form, change):
        old_obj = models.Campaign.objects.get(id=obj.id)
        obj.save()
        if obj.real_time_campaign_stop and not old_obj.real_time_campaign_stop:
            campaignstop.notify_initialize(obj)
        utils.k1_helper.update_ad_groups(
            models.AdGroup.objects.filter(campaign_id=obj.id)
            .select_related("campaign")
            .only("id", "campaign__account_id"),
            "CampaignAdmin.save_model",
        )
        self.log_custom_flags_event_to_slack(old_obj, obj, user=request.user.email)

    def save_formset(self, request, form, formset, change):
        if formset.model == models.AdGroup:
            instances = formset.save(commit=False)
            for instance in instances:
                instance.save(request)

            for obj in formset.deleted_objects:
                obj.delete()
        else:
            formset.save()

    def view_on_site(self, obj):
        return "/v2/analytics/campaign/{}?settings".format(obj.id)


# Source
class SourceAdmin(admin.ModelAdmin):
    form = SourceForm
    search_fields = ("name", "bidder_slug")
    list_display = (
        "name",
        "source_type",
        "tracking_slug",
        "bidder_slug",
        "maintenance",
        "deprecated",
        "released",
        "impression_trackers_count",
        "created_dt",
        "modified_dt",
    )
    autocomplete_fields = ("source_type",)
    readonly_fields = ("id", "created_dt", "modified_dt", "deprecated", "released", "source_actions")
    list_filter = ("maintenance", "deprecated", "released", "supports_video", "supports_display")

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            url(
                r"^(?P<source_id>.+)/release/$", self.admin_site.admin_view(self.release_source), name="release-source"
            ),
            url(
                r"^(?P<source_id>.+)/unrelease/$",
                self.admin_site.admin_view(self.unrelease_source),
                name="unrelease-source",
            ),
        ]
        return custom_urls + urls

    def source_actions(self, source):
        if source.id is None:
            return "Source not yet created"
        if source.released:
            return format_html(
                '<a class="button" href="{}">Unrelease</a>', reverse("admin:unrelease-source", args=[source.pk])
            )
        else:
            return format_html(
                '<a class="button" href="{}">Release</a>', reverse("admin:release-source", args=[source.pk])
            )

    source_actions.short_description = "Source Release Actions"

    def release_source(self, request, source_id, *args, **kwargs):
        return self.process_action(
            request,
            source_id,
            core.features.source_adoption.release_source,
            "Source successfully released and added to allowed sources on {} accounts. "
            "Please contact engineering to add the released source to ad groups of accounts "
            "which have automatic addition of newly released sources turned on.",
        )

    def unrelease_source(self, request, source_id, *args, **kwargs):
        return self.process_action(
            request, source_id, core.features.source_adoption.unrelease_source, "Source successfully unreleased."
        )

    def process_action(self, request, source_id, fn, message):
        source = self.get_object(request, source_id)

        try:
            allowed_count = fn(request, source)

        except (
            core.features.source_adoption.exceptions.SourceAlreadyReleased,
            core.features.source_adoption.exceptions.SourceAlreadyUnreleased,
        ) as err:
            messages.set_level(request, messages.ERROR)
            messages.error(request, str(err))

        else:
            self.message_user(request, message.format(allowed_count))

        url = reverse("admin:dash_source_change", args=[source.pk], current_app=self.admin_site.name)
        return HttpResponseRedirect(url)

    def get_queryset(self, request):
        qs = super(SourceAdmin, self).get_queryset(request)
        return qs.select_related("source_type")


# Source Type
class SourceTypeAdmin(admin.ModelAdmin):
    form = SourceTypeForm

    fields = (
        "type",
        "available_actions",
        "min_cpc",
        "min_cpm",
        "min_daily_budget",
        "max_cpc",
        "max_cpm",
        "max_daily_budget",
        "cpc_decimal_places",
        "delete_traffic_metrics_threshold",
    )
    search_fields = ("type", "id")

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ("type",)
        return self.readonly_fields

    class Media:
        css = {"all": ("css/admin/source_type_custom.css",)}


class SourceCredentialsAdmin(admin.ModelAdmin):
    form = SourceCredentialsForm
    verbose_name = "Source Credentials"
    verbose_name_plural = "Source Credentials"
    search_fields = ("name", "source")
    list_display = ("name", "source", "created_dt", "modified_dt")
    readonly_fields = ("created_dt", "modified_dt")
    autocomplete_fields = ("source",)


class CampaignSettingsAdmin(SaveWithRequestMixin, admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        return list(
            set(
                [field.name for field in self.opts.local_fields]
                + [field.name for field in self.opts.local_many_to_many]
            )
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "campaign_manager":
            kwargs["queryset"] = ZemUser.objects.all().order_by("last_name")

        return super(CampaignSettingsAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    actions = None

    search_fields = ("campaign__name",)
    list_display = ("campaign", "campaign_manager", "iab_category", "promotion_goal", "created_dt")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# Ad Group
class IsArchivedFilter(admin.SimpleListFilter):
    title = "Is archived"
    parameter_name = "is_archived"

    def lookups(self, request, model_admin):
        return ((1, "Archived"), (0, "Not archived"))

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset

        value_bool = self.value() == "1"

        related_settings = models.AdGroupSettings.objects.all().filter(ad_group__in=queryset).group_current_settings()

        ad_group_ids = (
            models.AdGroupSettings.objects.filter(pk__in=related_settings)
            .filter(archived=value_bool)
            .values_list("ad_group", flat=True)
        )

        return queryset.filter(pk__in=ad_group_ids)


class AdGroupAdmin(SlackLoggerMixin, admin.ModelAdmin):
    class Media:
        css = {"all": ("css/admin/style.css",)}

    search_fields = ("name",)
    list_display = ("id", "name", "campaign_", "account_", "is_archived_", "created_dt", "modified_dt")
    list_filter = [IsArchivedFilter]

    raw_id_fields = ("settings", "default_blacklist", "default_whitelist")
    readonly_fields = (
        "id",
        "name",
        "campaign",
        "created_dt",
        "modified_dt",
        "modified_by",
        "reset_approved_submission_statuses",
        "reset_rejected_submission_statuses",
    )
    exclude = ("settings",)
    form = dash_forms.AdGroupAdminForm
    inlines = (DirectDealConnectionAdGroupsInline,)

    fieldsets = (
        (
            None,
            {"fields": ("name", "campaign", "created_dt", "modified_dt", "modified_by", "entity_tags", "custom_flags")},
        ),
        (
            "Content ads submission statuses",
            {"fields": ("reset_approved_submission_statuses", "reset_rejected_submission_statuses")},
        ),
        (
            "Additional targeting",
            {"classes": ("collapse",), "fields": dash_forms.AdGroupAdminForm.ADDITIONAL_TARGETING_FIELDS},
        ),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super(AdGroupAdmin, self).get_form(request, obj=obj, **kwargs)
        form.request = request
        return form

    def get_queryset(self, request):
        qs = super(AdGroupAdmin, self).get_queryset(request)
        qs = qs.select_related("campaign__account")
        return qs

    def view_on_site(self, obj):
        return "/v2/analytics/adgroup/{}?settings".format(obj.id)

    def is_archived_(self, obj):
        try:
            last_settings = obj.current_settings[0]
            return bool(last_settings.archived)
        except Exception:
            pass
        return False

    is_archived_.short_description = "Is archived"
    is_archived_.boolean = True

    def save_model(self, request, ad_group, form, change):
        old_obj = models.AdGroup.objects.get(id=ad_group.id)
        current_settings = ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        for field in form.SETTINGS_FIELDS:
            value = form.cleaned_data.get(field)
            if getattr(new_settings, field) != value:
                setattr(new_settings, field, value)
        changes = current_settings.get_setting_changes(new_settings)
        if changes:
            new_settings.save(request)
            changes_text = new_settings.get_changes_text(current_settings, new_settings, request.user, separator="\n")
            utils.email_helper.send_ad_group_notification_email(ad_group, request, changes_text)
        ad_group.save(request)
        utils.k1_helper.update_ad_group(ad_group, msg="AdGroupAdmin.save_model")
        self.log_custom_flags_event_to_slack(old_obj, ad_group, user=request.user.email)

    def account_(self, obj):
        return mark_safe(
            '<a href="{account_url}">{account}</a>'.format(
                account_url=reverse("admin:dash_account_change", args=(obj.campaign.account.id,)),
                account=obj.campaign.account,
            )
        )

    account_.admin_order_field = "campaign__account"

    def campaign_(self, obj):
        return mark_safe(
            '<a href="{campaign_url}">{campaign}</a>'.format(
                campaign_url=reverse("admin:dash_campaign_change", args=(obj.campaign.id,)), campaign=obj.campaign
            )
        )

    campaign_.admin_order_field = "campaign"

    def reset_rejected(self, request, ad_group_id, *args, **kwargs):
        for cas in core.models.ContentAdSource.objects.filter(
            content_ad__ad_group=ad_group_id,
            submission_status=constants.ContentAdSubmissionStatus.REJECTED,
            source__source_type__type=constants.SourceType.OUTBRAIN,
        ):
            cas.submission_status = constants.ContentAdSubmissionStatus.PENDING
            cas.save()

        url = reverse("admin:dash_adgroup_change", args=[ad_group_id], current_app=self.admin_site.name)
        return HttpResponseRedirect(url)

    def reset_approved(self, request, ad_group_id, *args, **kwargs):
        for cas in core.models.ContentAdSource.objects.filter(
            content_ad__ad_group=ad_group_id,
            submission_status=constants.ContentAdSubmissionStatus.APPROVED,
            source__source_type__type=constants.SourceType.OUTBRAIN,
        ):
            cas.submission_status = constants.ContentAdSubmissionStatus.PENDING
            cas.save()

        url = reverse("admin:dash_adgroup_change", args=[ad_group_id], current_app=self.admin_site.name)
        return HttpResponseRedirect(url)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            url(
                r"^(?P<ad_group_id>.+)/reset-rejected/$",
                self.admin_site.admin_view(self.reset_rejected),
                name="reset-rejected",
            ),
            url(
                r"^(?P<ad_group_id>.+)/reset-approved/$",
                self.admin_site.admin_view(self.reset_approved),
                name="reset-approved",
            ),
        ]
        return custom_urls + urls

    def reset_approved_submission_statuses(self, ad_group):
        return format_html(
            '<a class="button" href="{}">Reset all approved</a>', reverse("admin:reset-approved", args=[ad_group.id])
        )

    def reset_rejected_submission_statuses(self, ad_group):
        return format_html(
            '<a class="button" href="{}">Reset all rejected</a>', reverse("admin:reset-rejected", args=[ad_group.id])
        )

    reset_approved_submission_statuses.short_description = "Reset approved content ads to pending on Amplify"
    reset_rejected_submission_statuses.short_description = "Reset rejected content ads to pending on Amplify"


# Ad Group Source
class AdGroupSourceAdmin(SaveWithRequestMixin, admin.ModelAdmin):
    list_display = ("ad_group_", "source_content_ad_id")
    exclude = ("settings",)
    search_fields = ("id", "name")

    list_filter = ("source",)

    def get_queryset(self, request):
        qs = super(AdGroupSourceAdmin, self).get_queryset(request)
        qs = qs.select_related("ad_group__campaign__account", "source")
        return qs

    def ad_group_(self, obj):
        return mark_safe(
            '<a href="{ad_group_url}">{name}</a>'.format(
                ad_group_url=reverse("admin:dash_adgroup_change", args=(obj.ad_group.id,)),
                name="{} / {} / {} - {} ({})".format(
                    obj.ad_group.campaign.account.name,
                    obj.ad_group.campaign.name,
                    obj.ad_group.name,
                    obj.source.name,
                    obj.ad_group.id,
                ),
            )
        )

    ad_group_.admin_order_field = "ad_group"


# Ad Group Settings
class AdGroupSettingsAdmin(SaveWithRequestMixin, admin.ModelAdmin):

    actions = None

    search_fields = ("ad_group__name",)
    list_display = ("ad_group", "state", "daily_budget_cc", "start_date", "end_date", "created_dt")
    readonly_fields = ("created_by", "ad_group")

    def has_delete_permission(self, request, obj=None):
        return False


class AdGroupSourceSettingsAdmin(admin.ModelAdmin):
    raw_id_fields = ("ad_group_source",)
    search_fields = ("ad_group_source__ad_group__name", "ad_group_source__source__name")
    list_display = ("ad_group_source", "state", "cpc_cc", "daily_budget_cc", "created_dt")
    readonly_fields = ("created_by",)


class AdGroupModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return "{} | {} | {}".format(obj.campaign.account.name, obj.campaign.name, obj.name)


# OutBrain Account
class OutbrainAccountAdmin(admin.ModelAdmin):
    list_display = ("marketer_id", "marketer_name", "used", "created_dt", "modified_dt")
    list_filter = ("used",)
    search_fields = ("marketer_name", "marketer_id")
    readonly_fields = ("_z1_account",)

    def _z1_account(self, obj):
        return mark_safe(
            ", ".join(
                '<a href="{account_url}">{account}</a>'.format(
                    account_url=reverse("admin:dash_account_change", args=(account.pk,)), account=account.name
                )
                for account in models.Account.objects.filter(outbrain_marketer_id=obj.marketer_id)
            )
        )


def reject_content_ad_sources(modeladmin, request, queryset):
    logger.info(
        "BULK REJECT CONTENT AD SOURCES: Bulk reject content ad sources started. Content ad sources: {}".format(
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
        messages.warning(
            request,
            "Marking content ad sources as rejected is only supported for the Outbrain source,\
                                   content ad sources with content ad ids {0} were ignored".format(
                ignored
            ),
        )


reject_content_ad_sources.short_description = "Mark selected content ad sources as REJECTED"


class ContentAdGroupSettingsStatusFilter(admin.SimpleListFilter):
    title = "Ad group status"
    parameter_name = "ad_group_settings_status"

    def lookups(self, request, model_admin):
        return constants.AdGroupSettingsState.get_choices()

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset

        queried_state = int(self.value())
        return queryset.filter(content_ad__ad_group__in=models.AdGroup.objects.filter(settings__state=queried_state))


def _resubmit_content_ad(queryset, clear=False):
    for cas in queryset.all():
        if clear:
            cas.source_content_ad_id = None
        cas.submission_status = -1
        cas.save()
        utils.k1_helper.update_content_ad(cas.content_ad, "content ad resubmit")


def resubmit_content_ads(modeladmin, request, queryset):
    logger.info(
        "BULK RESUBMIT CONTENT AD: Bulk resubmit content ad started. Content ad sources: {}".format(
            [el.id for el in queryset]
        )
    )
    _resubmit_content_ad(queryset, clear=True)


resubmit_content_ads.short_description = "Resubmit selected content ads"


class ContentAdSourceAdmin(admin.ModelAdmin):
    list_display = (
        "content_ad_id_",
        "source_content_ad_id",
        "ad_group_name",
        "ad_group_settings_status",
        "source",
        "submission_status_",
        "submission_errors",
        "created_dt",
        "modified_dt",
    )
    search_fields = (
        "content_ad__ad_group__name",
        "content_ad__ad_group__campaign__name",
        "content_ad__ad_group__campaign__account__name",
    )
    list_filter = ("source", "submission_status", ContentAdGroupSettingsStatusFilter)
    actions = [reject_content_ad_sources, resubmit_content_ads]

    display_submission_status_colors = {
        constants.ContentAdSubmissionStatus.APPROVED: "#5cb85c",
        constants.ContentAdSubmissionStatus.REJECTED: "#d9534f",
        constants.ContentAdSubmissionStatus.PENDING: "#428bca",
        constants.ContentAdSubmissionStatus.LIMIT_REACHED: "#e6c440",
        constants.ContentAdSubmissionStatus.NOT_SUBMITTED: "#bcbcbc",
    }

    def get_queryset(self, request):
        qs = super(ContentAdSourceAdmin, self).get_queryset(request)
        qs = qs.select_related("content_ad__ad_group__settings", "content_ad__ad_group__campaign__account", "source")
        return qs

    def has_add_permission(self, request):
        return False

    def submission_status_(self, obj):
        return mark_safe(
            '<span style="color:{color}">{submission_status}</span>'.format(
                color=self.display_submission_status_colors[obj.submission_status],
                submission_status=obj.get_submission_status_display(),
            )
        )

    submission_status_.admin_order_field = "submission_status"

    def content_ad_id_(self, obj):
        return obj.content_ad.id

    content_ad_id_.admin_order_field = "content_ad_id"

    def ad_group_name(self, obj):
        ad_group = obj.content_ad.ad_group
        return mark_safe(
            '<a href="{account_url}">{account_name}</a> / <a href="{campaign_url}">{campaign_name}</a>'
            ' / <a href="{ad_group_url}">{ad_group_name}</a> - ({ad_group_id})'.format(
                account_url=reverse("admin:dash_account_change", args=(ad_group.campaign.account.id,)),
                account_name=ad_group.campaign.account.name,
                campaign_url=reverse("admin:dash_campaign_change", args=(ad_group.campaign.id,)),
                campaign_name=ad_group.campaign.name,
                ad_group_url=reverse("admin:dash_adgroup_change", args=(ad_group.id,)),
                ad_group_name=ad_group.name,
                ad_group_id=str(ad_group.id),
            )
        )

    def ad_group_settings_status(self, obj):
        ad_group = obj.content_ad.ad_group
        ad_group_settings = ad_group.get_current_settings()
        return constants.AdGroupSettingsState.get_text(ad_group_settings.state)

    def save_model(self, request, content_ad_source, form, change):
        content_ad_source.save()
        utils.k1_helper.update_content_ad(content_ad_source.content_ad, msg="admin.content_ad_source")

    def __init__(self, *args, **kwargs):
        super(ContentAdSourceAdmin, self).__init__(*args, **kwargs)
        self.list_display_links = None


# Credit Line Item
class CreditLineItemResource(resources.ModelResource):
    class Meta:
        model = models.CreditLineItem

    def _get_name(self, obj):
        return obj.name if obj else "/"

    def dehydrate_account(self, obj):
        return obj.account.name if obj.account else "/"

    def dehydrate_created_by(self, obj):
        return obj.created_by.email if obj.created_by else "/"

    def dehydrate_status(self, obj):
        return constants.CreditLineItemStatus.get_text(obj.status)


class CreditLineItemAdmin(ExportMixin, SaveWithRequestMixin, admin.ModelAdmin):
    list_display = (
        "account",
        "agency",
        "start_date",
        "end_date",
        "currency",
        "amount",
        "status",
        "license_fee",
        "refund",
        "created_dt",
        "created_by",
    )
    date_hierarchy = "start_date"
    list_filter = ("status", "refund", "currency", "license_fee", "created_by")
    readonly_fields = ("contract_id", "contract_number", "created_dt", "created_by")
    search_fields = ("account__name", "agency__name", "amount")
    form = dash_forms.CreditLineItemAdminForm

    resource_class = CreditLineItemResource

    def get_queryset(self, request):
        qs = super(CreditLineItemAdmin, self).get_queryset(request)
        qs = qs.select_related("account", "agency", "created_by")
        return qs

    def get_actions(self, request):
        actions = super(CreditLineItemAdmin, self).get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    def has_delete_permission(self, request, obj=None):
        return False


# Refund
class RefundLineItemResource(resources.ModelResource):
    class Meta:
        model = models.RefundLineItem

    def _get_name(self, obj):
        return obj.name if obj else "/"

    def dehydrate_account(self, obj):
        return obj.account.name if obj.account else "/"

    def dehydrate_created_by(self, obj):
        return obj.created_by.email if obj.created_by else "/"


class RefundLineItemAdmin(ExportMixin, SaveWithRequestMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "account",
        "credit",
        "start_date",
        "end_date",
        "amount",
        "comment",
        "created_dt",
        "created_by",
    )
    date_hierarchy = "start_date"
    list_filter = ("account", "created_by", "credit")
    readonly_fields = ("id", "end_date", "created_dt", "created_by")
    search_fields = ("id", "account__name", "amount", "comment")
    autocomplete_fields = ("account", "credit")
    actions = None
    form = dash_forms.RefundLineItemAdminForm
    resource_class = RefundLineItemResource

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.select_related("account", "credit", "created_by")
        return qs

    def delete_model(self, request, refund):
        try:
            super().delete_model(request, refund)

        except models.refund_line_item.exceptions.CreditAvailableAmountNegative as err:
            messages.set_level(request, messages.ERROR)
            messages.error(request, str(err))


# Budgets
class BudgetLineItemAdmin(SaveWithRequestMixin, admin.ModelAdmin):
    list_display = (
        "__str__",
        "campaign",
        "start_date",
        "end_date",
        "amount",
        "service_fee",
        "license_fee",
        "created_dt",
    )
    date_hierarchy = "start_date"
    list_filter = ["created_by"]
    readonly_fields = ("created_dt", "created_by", "freed_cc")
    search_fields = ("campaign__name", "campaign__account__name", "amount")
    autocomplete_fields = ("credit",)
    raw_id_fields = ("campaign",)

    form = dash_forms.BudgetLineItemAdminForm


# Scheduled Reports
class ScheduledExportReportLogAdmin(admin.ModelAdmin):
    search_fields = ("scheduled_report",)
    list_display = (
        "created_dt",
        "start_date",
        "end_date",
        "state",
        "scheduled_report",
        "recipient_emails",
        "report_filename",
        "errors",
    )
    readonly_fields = ["created_dt"]
    autocomplete_fields = ("scheduled_report",)


class ScheduledExportReportAdmin(admin.ModelAdmin):
    search_fields = ("name", "created_by__email")
    list_display = (
        "created_dt",
        "created_by",
        "name",
        "report",
        "report_",
        "sending_frequency",
        "day_of_week",
        "time_period",
        "get_sources",
        "_agencies",
        "_account_types",
        "get_recipients",
        "state",
    )
    readonly_fields = ["created_dt", "created_by"]
    list_filter = ("state", "sending_frequency")
    ordering = ("state", "-created_dt")
    raw_id_fields = ("report",)

    def get_recipients(self, obj):
        return ", ".join(obj.get_recipients_emails_list())

    get_recipients.short_description = "Recipient Emails"

    def get_sources(self, obj):
        if len(obj.report.filtered_sources.all()) == 0:
            return "All Sources"
        return ", ".join(source.name for source in obj.report.get_filtered_sources())

    get_sources.short_description = "Filtered Sources"

    def report_(self, obj):
        link = reverse("admin:dash_exportreport_change", args=(obj.report.id,))
        return mark_safe('<a href="%s">%s</a>' % (link, obj.report))

    def _agencies(self, obj):
        if len(obj.report.filtered_agencies.all()) == 0:
            return "All Agencies"
        return ", ".join(agency.name for agency in obj.report.get_filtered_agencies())

    _agencies.short_description = "Filtered Agencies"

    def _account_types(self, obj):
        if len(obj.report.filtered_account_types or []) == 0:
            return "All Account Types"
        return ", ".join(account_type_name for account_type_name in obj.report.get_filtered_account_types())

    _agencies.short_description = "Filtered Account Types"


class ExportReportAdmin(admin.ModelAdmin):
    search_fields = ("created_by__email",)
    list_display = (
        "created_dt",
        "created_by",
        "granularity",
        "breakdown_by_day",
        "breakdown_by_source",
        "include_model_ids",
        "include_totals",
        "order_by",
        "ad_group",
        "campaign",
        "account",
        "additional_fields",
        "get_sources",
        "_agencies",
        "_account_types",
    )
    readonly_fields = ["created_dt"]
    autocomplete_fields = ("account",)

    def get_sources(self, obj):
        if len(obj.filtered_sources.all()) == 0:
            return "All Sources"
        return ", ".join(source.name for source in obj.get_filtered_sources())

    get_sources.short_description = "Filtered Sources"

    def _agencies(self, obj):
        if len(obj.filtered_agencies.all()) == 0:
            return "All Agencies"
        return ", ".join(agency.name for agency in obj.get_filtered_agencies())

    _agencies.short_description = "Filtered Agencies"

    def _account_types(self, obj):
        if len(obj.filtered_account_types or []) == 0:
            return "All Account Types"
        return ", ".join(account_type_name for account_type_name in obj.get_filtered_account_types())

    _agencies.short_description = "Filtered Account Types"


# Email Templates
class EmailTemplateAdmin(admin.ModelAdmin):
    actions = None

    list_display = ("template_type", "subject", "recipients")
    readonly_fields = ("template_type",)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["show_save"] = True
        extra_context["show_save_and_add_another"] = False
        extra_context["show_save_and_continue"] = True
        return super(EmailTemplateAdmin, self).change_view(request, object_id, form_url, extra_context=extra_context)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return True


class HistoryResource(resources.ModelResource):
    class Meta:
        model = models.History
        exclude = ["changes"]

    def _get_name(self, obj):
        return obj.name if obj else "/"

    def dehydrate_action_type(self, obj):
        if not obj.action_type:
            return "/"
        return constants.HistoryActionType.get_text(obj.action_type)

    def dehydrate_level(self, obj):
        return constants.HistoryLevel.get_text(obj.level)

    def dehydrate_ad_group(self, obj):
        return self._get_name(obj.ad_group)

    def dehydrate_campaign(self, obj):
        return self._get_name(obj.campaign)

    def dehydrate_account(self, obj):
        return self._get_name(obj.account)

    def dehydrate_agency(self, obj):
        return self._get_name(obj.agency)

    def dehydrate_created_by(self, obj):
        return obj.created_by.email if obj.created_by else "/"

    def dehydrate_system_user(self, obj):
        if not obj.system_user:
            return "/"
        return constants.SystemUserType.get_text(obj.system_user)


class SelfManagedFilter(SimpleListFilter):
    title = "Self Managed User"
    parameter_name = "created_by"

    def lookups(self, request, model_admin):
        return [("self-managed", "Self-Managed User"), ("system-user", "System User")]

    def queryset(self, request, queryset):
        if self.value() == "self-managed":
            return (
                queryset.filter(created_by__email__isnull=False)
                .exclude(created_by__email__icontains="@zemanta")
                .exclude(created_by__is_test_user=True)
                .exclude(action_type__isnull=True)
            )
        elif self.value() == "system-user":
            return queryset.filter(created_by__email__isnull=True)

        return queryset


class HistoryAdmin(ExportMixin, admin.ModelAdmin):
    actions = None

    list_display = (
        "id",
        "agency_",
        "account_",
        "campaign_",
        "ad_group_",
        "created_dt",
        "created_by",
        "system_user",
        "changes_text",
    )

    list_filter = (SelfManagedFilter, ("created_dt", admin.DateFieldListFilter), "action_type", "level", "system_user")

    search_fields = (
        "agency__id",
        "agency__name",
        "account__name",
        "account__id",
        "campaign__name",
        "campaign__id",
        "ad_group__name",
        "ad_group__id",
        "changes_text",
        "created_by__email",
    )

    ordering = ("-created_dt",)
    date_hierarchy = "created_dt"

    resource_class = HistoryResource

    def get_queryset(self, request):
        qs = super(HistoryAdmin, self).get_queryset(request)
        qs = qs.select_related("agency", "account", "campaign", "ad_group", "created_by")
        return qs

    def get_readonly_fields(self, request, obj=None):
        return list(
            set(
                [field.name for field in self.opts.local_fields]
                + [field.name for field in self.opts.local_many_to_many]
            )
        )

    def agency_(self, obj):
        return mark_safe(
            '<a href="{agency_url}">{agency}</a>'.format(
                agency_url=reverse("admin:dash_agency_change", args=(obj.agency.id,)), agency=obj.agency
            )
            if obj.agency
            else "-"
        )

    agency_.admin_order_field = "agency"

    def account_(self, obj):
        return mark_safe(
            '<a href="{account_url}">{account}</a>'.format(
                account_url=reverse("admin:dash_account_change", args=(obj.account.id,)), account=obj.account
            )
            if obj.account
            else "-"
        )

    account_.admin_order_field = "account"

    def campaign_(self, obj):
        return mark_safe(
            '<a href="{campaign_url}">{campaign}</a>'.format(
                campaign_url=reverse("admin:dash_campaign_change", args=(obj.campaign.id,)), campaign=obj.campaign
            )
            if obj.campaign
            else "-"
        )

    campaign_.admin_order_field = "campaign"

    def ad_group_(self, obj):
        return mark_safe(
            '<a href="{ad_group_url}">{ad_group}</a>'.format(
                ad_group_url=reverse("admin:dash_adgroup_change", args=(obj.ad_group.id,)), ad_group=obj.ad_group
            )
            if obj.ad_group
            else "-"
        )

    ad_group_.admin_order_field = "ad_group"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return True


# Audience
class AudienceRuleAdmin(admin.TabularInline):
    model = models.AudienceRule
    extra = 3


class AudienceAdmin(admin.ModelAdmin):
    list_display = ("pixel", "ttl", "prefill_days", "created_dt", "modified_dt")
    inlines = [AudienceRuleAdmin]
    exclude = ("ad_group_settings",)
    readonly_fields = ("created_by",)


# Publisher Group
class PublisherGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "account", "agency", "created_dt", "modified_dt")
    readonly_fields = ("modified_by",)
    search_fields = ("name",)
    autocomplete_fields = ("account", "agency")

    def get_queryset(self, request):
        qs = super(PublisherGroupAdmin, self).get_queryset(request)
        qs = qs.select_related("account", "agency")
        return qs

    def save_model(self, request, obj, form, change):
        obj.save(request)


# Publisher Group
class PublisherGroupListFilter(SimpleListFilter):
    title = "Publisher Group Type"
    parameter_name = "publisher_group_type"

    def lookups(self, request, model_admin):
        return (("global", "Global"),)

    def queryset(self, request, queryset):
        return queryset


class PublisherGroupEntryAdmin(ExportMixin, admin.ModelAdmin):
    list_display = (
        "publisher_group",
        "source",
        "publisher",
        "include_subdomains",
        "placement",
        "created_dt",
        "modified_dt",
    )
    readonly_fields = ("created_dt", "modified_dt")
    search_fields = ("publisher_group__name", "publisher_group__id", "publisher", "source__name")
    raw_id_fields = ("publisher_group",)
    autocomplete_fields = ("source",)

    list_filter = (("created_dt", admin.DateFieldListFilter), PublisherGroupListFilter, "source")

    def get_queryset(self, request):
        qs = super(PublisherGroupEntryAdmin, self).get_queryset(request)
        qs = qs.select_related("source", "publisher_group")
        return qs

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ("publisher_group",)
        return self.readonly_fields


# Publisher Classification
class PublisherClassificationAdmin(admin.ModelAdmin):
    list_display = ("pk", "publisher", "category", "toggle_ignore_")
    readonly_fields = ("pk", "created_dt", "modified_dt")
    search_fields = ("pk", "publisher", "category", "ignored", "created_dt", "modified_dt")

    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            url(
                r"^(?P<classification_id>.+)/ignore/$",
                self.admin_site.admin_view(self.ignore_classification),
                name="toggle-ignore-classification",
            )
        ]
        return custom_urls + urls

    def ignore_classification(self, request, classification_id):
        try:
            classification = self.get_object(request, classification_id)
            if classification.ignored is True:
                classification.ignored = False
            else:
                classification.ignored = True
            classification.save()
            self.message_user(
                request,
                "Publisher: '{}' with classification '{}' was {}".format(
                    classification.publisher, classification.category, classification.ignored and "ignored" or "valid"
                ),
            )
        except Exception as err:
            messages.set_level(request, messages.ERROR)
            messages.error(request, str(err))

        url = reverse("admin:dash_publisherclassification_changelist", current_app=self.admin_site.name)
        return HttpResponseRedirect(url)

    def toggle_ignore_(self, obj):
        link = reverse("admin:toggle-ignore-classification", args=(obj.id,))
        return mark_safe('<a href="%s">%s</a>' % (link, obj.ignored and "ignored" or "valid"))


# CPC constraints
class CpcConstraintAdmin(admin.ModelAdmin):
    model = models.CpcConstraint
    list_display = (
        "id",
        "source",
        "_agency",
        "_account",
        "_campaign",
        "ad_group",
        "min_cpc",
        "max_cpc",
        "constraint_type",
        "created_dt",
        "_reason",
    )

    list_filter = ("constraint_type", "source")

    search_fields = (
        "agency__id",
        "agency__name",
        "account__name",
        "account__id",
        "campaign__name",
        "campaign__id",
        "ad_group__name",
        "ad_group__id",
    )
    readonly_fields = ("created_dt",)
    raw_id_fields = ("agency", "account", "campaign", "ad_group")
    autocomplete_fields = ("source",)

    ordering = ("-created_dt",)
    date_hierarchy = "created_dt"

    def _reason(self, obj):
        if obj.reason is None:
            return ""
        if len(obj.reason) > 30:
            return obj.reason[:27] + " ..."
        return obj.reason

    def save_model(self, request, obj, form, change):
        cpc_constraints.enforce_rule(
            obj.min_cpc,
            obj.max_cpc,
            **{
                lvl: getattr(obj, lvl)
                for lvl in ("agency", "account", "campaign", "ad_group", "source")
                if getattr(obj, lvl) is not None
            },
        )
        obj.save()

    def get_queryset(self, request):
        qs = super(CpcConstraintAdmin, self).get_queryset(request)
        return qs.select_related(
            "ad_group__campaign__account__agency", "campaign__account__agency", "account__agency", "agency", "source"
        )

    def _agency(self, obj):
        return (
            obj.agency
            or (obj.account and obj.account.agency)
            or (obj.campaign and obj.campaign.account and obj.campaign.account.agency)
            or (
                obj.ad_group
                and obj.ad_group.campaign
                and obj.ad_group.campaign.account
                and obj.ad_group.campaign.account.agency
            )
            or None
        )

    def _account(self, obj):
        return (
            obj.account
            or (obj.campaign and obj.campaign.account)
            or (obj.ad_group and obj.ad_group.campaign and obj.ad_group.campaign.account)
            or None
        )

    def _campaign(self, obj):
        return obj.campaign or (obj.ad_group and obj.ad_group.campaign) or None


# Custom Hacks
class CustomHackStatusFilter(SimpleListFilter):
    title = "Status"
    parameter_name = "removed_dt"

    def lookups(self, request, model_admin):
        return [
            ("active", "Active"),
            ("confirmed", "Confirmed"),
            ("unconfirmed", "Unconfirmed"),
            ("removed", "Removed"),
        ]

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        elif self.value() == "confirmed":
            queryset = queryset.filter(confirmed_by__isnull=False)
        elif self.value() == "unconfirmed":
            queryset = queryset.filter(confirmed_by__isnull=True)
        return queryset.filter_active(self.value() != "removed")


class CustomHackClientFilter(SimpleListFilter):
    title = "Client level"
    parameter_name = "client_level"

    def lookups(self, request, model_admin):
        return [
            ("global", "Global"),
            ("ad-group", "Ad Group"),
            ("campaign", "Campaign"),
            ("account", "Account"),
            ("agency", "Agency"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "global":
            queryset = queryset.filter(
                agency_id__isnull=True, account_id__isnull=True, campaign_id__isnull=True, ad_group_id__isnull=True
            )
        elif self.value() == "ad-group":
            queryset = queryset.filter(
                agency_id__isnull=True, account_id__isnull=True, campaign_id__isnull=True, ad_group_id__isnull=False
            )
        elif self.value() == "campaign":
            queryset = queryset.filter(
                agency_id__isnull=True, account_id__isnull=True, campaign_id__isnull=False, ad_group_id__isnull=True
            )
        elif self.value() == "account":
            queryset = queryset.filter(
                agency_id__isnull=True, account_id__isnull=False, campaign_id__isnull=True, ad_group_id__isnull=True
            )
        elif self.value() == "agency":
            queryset = queryset.filter(
                agency_id__isnull=False, account_id__isnull=True, campaign_id__isnull=True, ad_group_id__isnull=True
            )
        return queryset


class CustomHackAdmin(admin.ModelAdmin):
    model = models.CustomHack
    list_display = (
        "summary",
        "_active",
        "_source",
        "_agency",
        "_account",
        "_campaign",
        "_ad_group",
        "service",
        "created_dt",
    )

    list_filter = (CustomHackStatusFilter, CustomHackClientFilter, "summary", "service", "rtb_only", "source")

    search_fields = (
        "agency__id",
        "agency__name",
        "account__name",
        "account__id",
        "campaign__name",
        "campaign__id",
        "ad_group__name",
        "ad_group__id",
        "source__name",
    )

    readonly_fields = ("created_dt", "created_by", "confirmed_by", "confirmed_dt")
    raw_id_fields = ("agency", "account", "campaign", "ad_group")

    ordering = ("-created_dt",)
    date_hierarchy = "created_dt"
    autocomplete_fields = ("source",)

    def mark_removed(self, request, queryset):
        queryset.update(removed_dt=datetime.datetime.now())

    mark_removed.short_description = "Mark removed"

    def mark_confirmed(self, request, queryset):
        queryset.update(confirmed_dt=datetime.datetime.now(), confirmed_by=request.user)

    mark_confirmed.short_description = "Mark confirmed"

    actions = (mark_removed, mark_confirmed)

    def get_queryset(self, request):
        qs = super(CustomHackAdmin, self).get_queryset(request)
        return qs.select_related(
            "ad_group__campaign__account__agency", "campaign__account__agency", "account__agency", "agency", "source"
        )

    def save_model(self, request, obj, form, change):
        obj.save(request)

    def _active(self, obj):
        return obj.removed_dt is None or obj.removed_dt > datetime.datetime.now()

    _active.boolean = True

    def _source(self, obj):
        if obj.rtb_only:
            return "RTB"
        return obj.source

    def _agency(self, obj):
        entity = (
            obj.agency
            or (obj.account and obj.account.agency)
            or (obj.campaign and obj.campaign.account and obj.campaign.account.agency)
            or (
                obj.ad_group
                and obj.ad_group.campaign
                and obj.ad_group.campaign.account
                and obj.ad_group.campaign.account.agency
            )
            or None
        )
        return entity and "{} | {}".format(entity.pk, str(entity.name)) or ""

    def _account(self, obj):
        entity = (
            obj.account
            or (obj.campaign and obj.campaign.account)
            or (obj.ad_group and obj.ad_group.campaign and obj.ad_group.campaign.account)
            or None
        )
        return entity and "{} | {}".format(entity.pk, str(entity.name)) or ""

    def _campaign(self, obj):
        entity = obj.campaign or (obj.ad_group and obj.ad_group.campaign) or ""
        return entity and "{} | {}".format(entity.pk, str(entity.name)) or ""

    def _ad_group(self, obj):
        return obj.ad_group and "{} | {}".format(obj.ad_group.pk, str(obj.ad_group.name)) or ""


# Custom Flags
class CustomFlagAdmin(admin.ModelAdmin):
    model = models.CustomFlag

    list_display = ("id", "name", "description", "advanced")

    def get_actions(self, request):
        actions = super(CustomFlagAdmin, self).get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions


# Deals
class DirectDealConnectionAdmin(admin.ModelAdmin):
    model = models.DirectDealConnection
    form = dash_forms.DirectDealConnectionAdminForm
    raw_id_fields = ("adgroup", "campaign")
    readonly_fields = ("id", "modified_dt", "created_dt", "created_by", "modified_by")
    list_display = ("id", "source", "exclusive", "is_global", "agency", "account", "campaign", "adgroup", "deal_id")
    search_fields = ("deal__source__name", "deal__deal_id", "adgroup__id", "campaign__id", "account__id", "agency__id")
    autocomplete_fields = ("agency", "account", "deal")

    def deal_id(self, obj):
        return obj.deal.deal_id

    def source(self, obj):
        return obj.deal.source.name

    # Workaround to have boolean value displayed as an icon instead of a text.
    def is_global(self, obj):
        if obj.is_global:
            return True
        return False

    is_global.boolean = True

    def save_model(self, request, obj, form, change):
        obj.save(request)

    def delete_model(self, request, obj):
        obj.delete(request)


class DirectDealAdmin(admin.ModelAdmin):
    model = models.DirectDeal
    readonly_fields = ("id", "modified_dt", "created_dt", "created_by", "modified_by")
    list_display = ("deal_id", "name", "source", "agency", "account", "floor_price", "valid_from_date", "valid_to_date")
    search_fields = ("id", "deal_id", "name", "agency__name", "account__name", "source__name")

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        try:
            return super(DirectDealAdmin, self).changeform_view(request, object_id, form_url, extra_context)
        except utils.exc.ValidationError as e:
            self.message_user(request, str(e.errors), level=messages.ERROR)
            return HttpResponseRedirect(request.path)

    def save_model(self, request, obj, form, change):
        obj.save(request)


class EntityTagAdmin(admin.ModelAdmin):
    model = tags.EntityTag


class CreativeTagAdmin(admin.ModelAdmin):
    model = tags.CreativeTag

    fields = ("name", "agency", "account")
    search_fields = ("id", "name", "agency__name", "account__name")
    list_display = ("id", "name", "agency", "account")
    autocomplete_fields = ("agency", "account")

    def get_queryset(self, request):
        qs = super(CreativeTagAdmin, self).get_queryset(request)
        qs = qs.select_related("agency", "account")
        return qs

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        try:
            return super(CreativeTagAdmin, self).changeform_view(request, object_id, form_url, extra_context)
        except utils.exc.ValidationError as e:
            self.message_user(request, str(e.errors), level=messages.ERROR)
            return HttpResponseRedirect(request.path)


class WhiteLabelAdmin(admin.ModelAdmin):
    model = models.WhiteLabel


tagulous.admin.register(models.Agency, AgencyAdmin)
tagulous.admin.register(models.Account, AccountAdmin)
tagulous.admin.register(models.Campaign, CampaignAdmin)
admin.site.register(models.CampaignSettings, CampaignSettingsAdmin)
tagulous.admin.register(models.Source, SourceAdmin)
tagulous.admin.register(models.AdGroup, AdGroupAdmin)
admin.site.register(models.AdGroupSource, AdGroupSourceAdmin)
admin.site.register(models.AdGroupSettings, AdGroupSettingsAdmin)
admin.site.register(models.AdGroupSourceSettings, AdGroupSourceSettingsAdmin)
admin.site.register(models.SourceCredentials, SourceCredentialsAdmin)
admin.site.register(models.SourceType, SourceTypeAdmin)
admin.site.register(models.DefaultSourceSettings, DefaultSourceSettingsAdmin)
admin.site.register(models.OutbrainAccount, OutbrainAccountAdmin)
admin.site.register(models.ContentAdSource, ContentAdSourceAdmin)
admin.site.register(models.CreditLineItem, CreditLineItemAdmin)
admin.site.register(models.RefundLineItem, RefundLineItemAdmin)
admin.site.register(models.BudgetLineItem, BudgetLineItemAdmin)
admin.site.register(models.ScheduledExportReportLog, ScheduledExportReportLogAdmin)
admin.site.register(models.ScheduledExportReport, ScheduledExportReportAdmin)
admin.site.register(models.ExportReport, ExportReportAdmin)
admin.site.register(models.EmailTemplate, EmailTemplateAdmin)
admin.site.register(models.History, HistoryAdmin)
admin.site.register(models.Audience, AudienceAdmin)
admin.site.register(models.PublisherGroup, PublisherGroupAdmin)
admin.site.register(models.PublisherGroupEntry, PublisherGroupEntryAdmin)
admin.site.register(models.PublisherClassification, PublisherClassificationAdmin)
admin.site.register(models.CpcConstraint, CpcConstraintAdmin)
admin.site.register(models.CustomHack, CustomHackAdmin)
admin.site.register(models.CustomFlag, CustomFlagAdmin)
admin.site.register(models.SubmissionFilter, SubmissionFilterAdmin)
admin.site.register(models.DirectDeal, DirectDealAdmin)
admin.site.register(models.DirectDealConnection, DirectDealConnectionAdmin)
admin.site.register(models.WhiteLabel, WhiteLabelAdmin)
admin.site.register(tags.CreativeTag, CreativeTagAdmin)
tagulous.admin.register(tags.EntityTag, EntityTagAdmin)
