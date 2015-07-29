import json
import logging
import newrelic.agent

from collections import OrderedDict
from decimal import Decimal
from django.db import transaction
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth import models as authmodels

from actionlog import api as actionlog_api
from actionlog import models as actionlog_models
from actionlog import constants as actionlog_constants
from actionlog import zwei_actions
from dash.views import helpers
from dash import forms
from dash import models
from dash import api
from dash import budget
from dash import constants
from utils import api_common
from utils import statsd_helper
from utils import exc
from utils import pagerduty_helper
from utils import email_helper

from zemauth.models import User as ZemUser


logger = logging.getLogger(__name__)


def get_campaign_url(ad_group, request):
    campaign_settings_url = request.build_absolute_uri(
        reverse('admin:dash_campaign_change', args=(ad_group.campaign.pk,)))
    campaign_settings_url = campaign_settings_url.replace('http://', 'https://')

    return campaign_settings_url


def send_ad_group_settings_change_mail_if_necessary(ad_group, user, request):
    if not settings.SEND_AD_GROUP_SETTINGS_CHANGE_MAIL:
        return

    campaign_settings = models.CampaignSettings.objects.\
        filter(campaign=ad_group.campaign).\
        order_by('-created_dt')[:1]

    if not campaign_settings or not campaign_settings[0].account_manager:
        logger.error('Could not send e-mail because there is no account manager set for campaign with id %s.', ad_group.campaign.pk)

        desc = {
            'campaign_settings_url': get_campaign_url(ad_group, request)
        }
        pagerduty_helper.trigger(
            event_type=pagerduty_helper.PagerDutyEventType.ADOPS,
            incident_key='ad_group_settings_change_mail_failed',
            description='E-mail notification for ad group settings change was not sent because the campaign settings or account manager is not set.',
            details=desc,
        )
        return

    if user.pk == campaign_settings[0].account_manager.pk:
        return

    email_helper.send_ad_group_settings_change_email(
        user,
        campaign_settings[0].account_manager,
        request,
        ad_group,
        get_campaign_url(ad_group, request)
    )


class AdGroupSettings(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_settings_get')
    def get(self, request, ad_group_id):
        if not request.user.has_perm('dash.settings_view'):
            raise exc.MissingDataError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        active_ad_group_sources = helpers.get_active_ad_group_sources(models.AdGroup, [ad_group])
        ad_group_sources_states = helpers.get_ad_group_sources_states(active_ad_group_sources)

        ad_group_sources = []
        for source_state in ad_group_sources_states:
            ad_group_sources.append({
                'id': source_state.ad_group_source.id,
                'source_state': source_state.state,
                'source_name': source_state.ad_group_source.source.name,
                'supports_dma_targeting': source_state.ad_group_source.source.source_type.supports_dma_targeting()
            })

        settings = ad_group.get_current_settings()

        response = {
            'settings': self.get_dict(settings, ad_group),
            'action_is_waiting': actionlog_api.is_waiting_for_set_actions(ad_group),
            'ad_group_sources': ad_group_sources
        }

        return self.create_api_response(response)

    @statsd_helper.statsd_timer('dash.api', 'ad_group_settings_put')
    def put(self, request, ad_group_id):
        if not request.user.has_perm('dash.settings_view'):
            raise exc.MissingDataError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id, select_related=True)
        previous_ad_group_name = ad_group.name

        current_settings = ad_group.get_current_settings()

        resource = json.loads(request.body)

        form = forms.AdGroupSettingsForm(resource.get('settings', {}))
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        self.set_ad_group(ad_group, form.cleaned_data)

        settings = current_settings.copy_settings()
        self.set_settings(settings, form.cleaned_data,
                          request.user.has_perm('zemauth.can_toggle_ga_performance_tracking'))

        actionlogs_to_send = []
        with transaction.atomic():
            order = actionlog_models.ActionLogOrder.objects.create(
                order_type=actionlog_constants.ActionLogOrderType.AD_GROUP_SETTINGS_UPDATE
            )
            ad_group.save(request)
            settings.save(request)

            if current_settings.state == constants.AdGroupSettingsState.INACTIVE \
                    and settings.state == constants.AdGroupSettingsState.ACTIVE:
                actionlogs_to_send.extend(actionlog_api.init_enable_ad_group(
                    ad_group, request, order=order, send=False))

            if current_settings.state == constants.AdGroupSettingsState.ACTIVE \
                    and settings.state == constants.AdGroupSettingsState.INACTIVE:
                actionlogs_to_send.extend(actionlog_api.init_pause_ad_group(
                    ad_group, request, order=order, send=False))

            current_settings.ad_group_name = previous_ad_group_name
            settings.ad_group_name = ad_group.name

            actionlogs_to_send.extend(api.order_ad_group_settings_update(ad_group, current_settings, settings, request, send=False))

        user = request.user
        changes = current_settings.get_setting_changes(settings)
        if changes:
            send_ad_group_settings_change_mail_if_necessary(ad_group, user, request)

        zwei_actions.send_multiple(actionlogs_to_send)

        response = {
            'settings': self.get_dict(settings, ad_group),
            'action_is_waiting': actionlog_api.is_waiting_for_set_actions(ad_group)
        }

        return self.create_api_response(response)

    def get_dict(self, settings, ad_group):
        result = {}

        if settings:
            result = {
                'id': str(ad_group.pk),
                'name': ad_group.name,
                'state': settings.state,
                'start_date': settings.start_date,
                'end_date': settings.end_date,
                'cpc_cc':
                    '{:.2f}'.format(settings.cpc_cc)
                    if settings.cpc_cc is not None else '',
                'daily_budget_cc':
                    '{:.2f}'.format(settings.daily_budget_cc)
                    if settings.daily_budget_cc is not None else '',
                'target_devices': settings.target_devices,
                'target_regions': settings.target_regions,
                'tracking_code': settings.tracking_code,
                'enable_ga_tracking': settings.enable_ga_tracking
            }

        return result

    def set_ad_group(self, ad_group, resource):
        ad_group.name = resource['name']

    def set_settings(self, settings, resource, can_set_tracking_codes):
        settings.state = resource['state']
        settings.start_date = resource['start_date']
        settings.end_date = resource['end_date']
        settings.cpc_cc = resource['cpc_cc']
        settings.daily_budget_cc = resource['daily_budget_cc']
        settings.target_devices = resource['target_devices']
        settings.target_regions = resource['target_regions']
        settings.ad_group_name = resource['name']
        if can_set_tracking_codes:
            settings.enable_ga_tracking = resource['enable_ga_tracking']
            settings.tracking_code = resource['tracking_code']


class CampaignSettings(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'campaign_settings_get')
    def get(self, request, campaign_id):
        if not request.user.has_perm('zemauth.campaign_settings_view'):
            raise exc.MissingDataError()

        campaign = helpers.get_campaign(request.user, campaign_id)

        campaign_settings = campaign.get_current_settings()

        response = {
            'settings': self.get_dict(campaign_settings, campaign),
            'account_managers': self.get_user_list(campaign_settings, 'campaign_settings_account_manager'),
            'sales_reps': self.get_user_list(campaign_settings, 'campaign_settings_sales_rep'),
            'history': self.get_history(campaign),
            'can_archive': campaign.can_archive(),
            'can_restore': campaign.can_restore(),
        }

        return self.create_api_response(response)

    @statsd_helper.statsd_timer('dash.api', 'campaign_settings_put')
    def put(self, request, campaign_id):
        if not request.user.has_perm('zemauth.campaign_settings_view'):
            raise exc.MissingDataError()

        campaign = helpers.get_campaign(request.user, campaign_id)

        resource = json.loads(request.body)

        form = forms.CampaignSettingsForm(resource.get('settings', {}))
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        self.set_campaign(campaign, form.cleaned_data)

        settings = models.CampaignSettings()
        self.set_settings(settings, campaign, form.cleaned_data)

        actions = []
        with transaction.atomic():
            campaign.save(request)
            settings.save(request)
            # propagate setting changes to all adgroups(adgroup sources) belonging to campaign
            campaign_ad_groups = models.AdGroup.objects.filter(campaign=campaign)

            for ad_group in campaign_ad_groups:
                adgroup_settings = ad_group.get_current_settings()
                actions.extend(
                    api.order_ad_group_settings_update(
                        ad_group,
                        adgroup_settings,
                        adgroup_settings,
                        request,
                        send=False,
                        iab_update=True
                    )
                )

        zwei_actions.send_multiple(actions)

        response = {
            'settings': self.get_dict(settings, campaign),
            'history': self.get_history(campaign),
            'can_archive': campaign.can_archive(),
            'can_restore': campaign.can_restore(),
        }

        return self.create_api_response(response)

    def get_history(self, campaign):
        settings = models.CampaignSettings.objects.\
            filter(campaign=campaign).\
            order_by('created_dt')

        history = []
        for i in range(0, len(settings)):
            old_settings = settings[i - 1] if i > 0 else None
            new_settings = settings[i]

            changes = old_settings.get_setting_changes(new_settings) \
                if old_settings is not None else None

            if i > 0 and not changes:
                continue

            settings_dict = self.convert_settings_to_dict(old_settings, new_settings)

            history.append({
                'datetime': new_settings.created_dt,
                'changed_by': new_settings.created_by.email,
                'changes_text': self.convert_changes_to_string(changes, settings_dict),
                'settings': settings_dict.values(),
                'show_old_settings': old_settings is not None
            })

        return history

    def format_decimal_to_percent(self, num):
        return '{:.2f}'.format(num * 100).rstrip('0').rstrip('.')

    def get_full_name_or_email(self, user):
        if user is None:
            return '/'

        result = user.get_full_name() or user.email
        return result.encode('utf-8')

    def convert_settings_to_dict(self, old_settings, new_settings):
        settings_dict = OrderedDict([
            ('name', {
                'name': 'Name',
                'value': new_settings.name.encode('utf-8')
            }),
            ('account_manager', {
                'name': 'Account Manager',
                'value': self.get_full_name_or_email(new_settings.account_manager)
            }),
            ('sales_representative', {
                'name': 'Sales Representative',
                'value': self.get_full_name_or_email(new_settings.sales_representative)
            }),
            ('service_fee', {
                'name': 'Service Fee',
                'value': self.format_decimal_to_percent(new_settings.service_fee) + '%'
            }),
            ('iab_category', {
                'name': 'IAB Category',
                'value': constants.IABCategory.get_text(new_settings.iab_category)
            }),
            ('promotion_goal', {
                'name': 'Promotion Goal',
                'value': constants.PromotionGoal.get_text(new_settings.promotion_goal)
            }),
            ('archived', {
                'name': 'Archived',
                'value': str(new_settings.archived)
            }),
        ])

        if old_settings is not None:
            settings_dict['name']['old_value'] = old_settings.name.encode('utf-8')

            if old_settings.account_manager is not None:
                settings_dict['account_manager']['old_value'] = \
                    self.get_full_name_or_email(old_settings.account_manager)

            if old_settings.sales_representative is not None:
                settings_dict['sales_representative']['old_value'] = \
                    self.get_full_name_or_email(old_settings.sales_representative)

            settings_dict['service_fee']['old_value'] = \
                self.format_decimal_to_percent(old_settings.service_fee) + '%'

            settings_dict['iab_category']['old_value'] = \
                constants.IABCategory.get_text(old_settings.iab_category)

            settings_dict['promotion_goal']['old_value'] = \
                constants.PromotionGoal.get_text(old_settings.promotion_goal)

            settings_dict['archived']['old_value'] = str(old_settings.archived)

        return settings_dict

    def convert_changes_to_string(self, changes, settings_dict):
        if changes is None:
            return 'Created settings'

        change_strings = []

        for key in changes:
            setting = settings_dict[key]
            change_strings.append(
                '{} set to "{}"'.format(setting['name'], setting['value'])
            )

        return ', '.join(change_strings)

    def get_dict(self, settings, campaign):
        result = {}

        if settings:
            result = {
                'id': str(campaign.pk),
                'name': campaign.name,
                'account_manager':
                    str(settings.account_manager.id)
                    if settings.account_manager is not None else None,
                'sales_representative':
                    str(settings.sales_representative.id)
                    if settings.sales_representative is not None else None,
                'service_fee': self.format_decimal_to_percent(settings.service_fee),
                'iab_category': settings.iab_category,
                'promotion_goal': settings.promotion_goal
            }

        return result

    def set_campaign(self, campaign, resource):
        campaign.name = resource['name']

    def set_settings(self, settings, campaign, resource):
        settings.campaign = campaign
        settings.name = resource['name']
        settings.account_manager = resource['account_manager']
        settings.sales_representative = resource['sales_representative']
        settings.service_fee = Decimal(resource['service_fee']) / 100
        settings.iab_category = resource['iab_category']
        settings.promotion_goal = resource['promotion_goal']

    def get_user_list(self, settings, perm_name):
        users = list(ZemUser.objects.get_users_with_perm(perm_name))

        manager = settings.account_manager
        if manager is not None and manager not in users:
            users.append(manager)

        return [{'id': str(user.id), 'name': self.get_full_name_or_email(user)} for user in users]


class CampaignBudget(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'campaign_budget_get')
    def get(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        response = self.get_response(campaign)
        return self.create_api_response(response)

    @statsd_helper.statsd_timer('dash.api', 'campaign_budget_put')
    def put(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        campaign_budget = budget.CampaignBudget(campaign)

        budget_change = json.loads(request.body)

        form = forms.CampaignBudgetForm(budget_change)

        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        campaign_budget.edit(
            allocate_amount=form.get_allocate_amount(),
            revoke_amount=form.get_revoke_amount(),
            request=request,
            comment='',
        )

        response = self.get_response(campaign)

        return self.create_api_response(response)

    def get_response(self, campaign):
        campaign_budget = budget.CampaignBudget(campaign)

        total = campaign_budget.get_total()
        spend = campaign_budget.get_spend()
        available = total - spend

        response = {
            'total': total,
            'available': available,
            'spend': spend,
            'history': self.format_history(campaign_budget.get_history())
        }
        return response

    def format_history(self, history):
        result = []
        for h in history:
            item = {}
            item['datetime'] = h.created_dt
            item['user'] = h.created_by.email
            item['allocate'] = float(h.allocate)
            item['revoke'] = float(h.revoke)
            item['total'] = float(h.total)
            item['comment'] = h.comment
            result.append(item)
        return result


class AccountAgency(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'account_agency_get')
    def get(self, request, account_id):
        if not request.user.has_perm('zemauth.account_agency_view'):
            raise exc.MissingDataError()

        account = helpers.get_account(request.user, account_id)
        account_settings = account.get_current_settings()

        response = {
            'settings': self.get_dict(account_settings, account),
            'history': self.get_history(account),
            'can_archive': account.can_archive(),
            'can_restore': account.can_restore(),
        }

        return self.create_api_response(response)

    @statsd_helper.statsd_timer('dash.api', 'account_agency_put')
    def put(self, request, account_id):
        if not request.user.has_perm('zemauth.account_agency_view'):
            raise exc.MissingDataError()

        account = helpers.get_account(request.user, account_id)

        resource = json.loads(request.body)

        form = forms.AccountAgencySettingsForm(resource.get('settings', {}))
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        self.set_account(account, form.cleaned_data)

        settings = models.AccountSettings()
        self.set_settings(settings, account, form.cleaned_data)

        with transaction.atomic():
            account.save(request)
            settings.save(request)

        response = {
            'settings': self.get_dict(settings, account),
            'history': self.get_history(account),
            'can_archive': account.can_archive(),
            'can_restore': account.can_restore(),
        }

        return self.create_api_response(response)

    def set_account(self, account, resource):
        account.name = resource['name']

    def set_settings(self, settings, account, resource):
        settings.account = account
        settings.name = resource['name']

    def get_dict(self, settings, account):
        result = {}

        if settings:
            result = {
                'id': str(account.pk),
                'name': account.name,
                'archived': settings.archived,
            }

        return result

    def get_history(self, account):
        settings = models.AccountSettings.objects.\
            filter(account=account).\
            order_by('created_dt')

        history = []
        for i in range(0, len(settings)):
            old_settings = settings[i - 1] if i > 0 else None
            new_settings = settings[i]

            settings_dict = self.convert_settings_to_dict(old_settings, new_settings)

            changes_text = new_settings.changes_text
            if changes_text is None:
                changes = old_settings.get_setting_changes(new_settings) \
                    if old_settings is not None else None

                if i > 0 and not changes:
                    continue

                changes_text = self.convert_changes_to_string(changes, settings_dict)

            history.append({
                'datetime': new_settings.created_dt,
                'changed_by': new_settings.created_by.email,
                'changes_text': changes_text,
                'settings': settings_dict.values(),
                'show_old_settings': old_settings is not None
            })

        return history

    def convert_changes_to_string(self, changes, settings_dict):
        if changes is None:
            return 'Created settings'

        change_strings = []

        for key in changes:
            setting = settings_dict[key]
            change_strings.append(
                '{} set to "{}"'.format(setting['name'], setting['value'])
            )

        return ', '.join(change_strings)

    def convert_settings_to_dict(self, old_settings, new_settings):
        settings_dict = OrderedDict([
            ('name', {
                'name': 'Name',
                'value': new_settings.name.encode('utf-8')
            }),
            ('archived', {
                'name': 'Archived',
                'value': str(new_settings.archived)
            }),
        ])

        if old_settings is not None:
            settings_dict['name']['old_value'] = old_settings.name.encode('utf-8')
            settings_dict['archived']['old_value'] = str(old_settings.archived)

        return settings_dict


class AdGroupAgency(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_agency_get')
    def get(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.ad_group_agency_tab_view'):
            raise exc.MissingDataError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        response = {
            'settings': {},
            'history': self.get_history(ad_group, request.user),
            'can_archive': ad_group.can_archive(),
            'can_restore': ad_group.can_restore(),
        }

        return self.create_api_response(response)

    @statsd_helper.statsd_timer('dash.api', 'ad_group_settings_put')
    def put(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.ad_group_agency_tab_view'):
            raise exc.MissingDataError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        previous_ad_group_name = ad_group.name

        current_settings = ad_group.get_current_settings()

        resource = json.loads(request.body)

        form = forms.AdGroupAgencySettingsForm(resource.get('settings', {}))
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        settings = current_settings.copy_settings()
        settings.tracking_code = form.cleaned_data['tracking_code']

        actions = []
        with transaction.atomic():
            settings.save(request)

            current_settings.ad_group_name = previous_ad_group_name
            settings.ad_group_name = ad_group.name
            actions = api.order_ad_group_settings_update(
                ad_group, current_settings, settings, request, send=False)

        zwei_actions.send_multiple(actions)

        user = request.user
        changes = current_settings.get_setting_changes(settings)
        if changes:
            send_ad_group_settings_change_mail_if_necessary(ad_group, user, request)

        response = {
            'settings': self.get_dict(settings, ad_group),
            'action_is_waiting': actionlog_api.is_waiting_for_set_actions(ad_group),
            'history': self.get_history(ad_group, request.user),
            'can_archive': ad_group.can_archive(),
            'can_restore': ad_group.can_restore(),
        }

        return self.create_api_response(response)

    @newrelic.agent.function_trace()
    def get_history(self, ad_group, user):
        settings = models.AdGroupSettings.objects.\
            filter(ad_group=ad_group).\
            order_by('created_dt')

        history = []
        for i in range(0, len(settings)):
            old_settings = settings[i - 1] if i > 0 else None
            new_settings = settings[i]

            changes = old_settings.get_setting_changes(new_settings) \
                if old_settings is not None else None

            if new_settings.changes_text is not None:
                changes_text = new_settings.changes_text
            else:
                changes_text = self.convert_changes_to_string(changes, user)

            if i > 0 and not len(changes_text):
                continue

            settings_dict = self.convert_settings_to_dict(old_settings, new_settings, user)

            history.append({
                'datetime': new_settings.created_dt,
                'changed_by': new_settings.created_by.email,
                'changes_text': changes_text,
                'settings': settings_dict.values(),
                'show_old_settings': old_settings is not None
            })

        return history

    @newrelic.agent.function_trace()
    def convert_changes_to_string(self, changes, user):
        if changes is None:
            return 'Created settings'

        change_strings = []

        for key, value in changes.iteritems():
            if key in ['display_url', 'brand_name', 'description', 'call_to_action'] and\
                    not user.has_perm('zemauth.new_content_ads_tab'):
                continue

            prop = models.AdGroupSettings.get_human_prop_name(key)
            val = models.AdGroupSettings.get_human_value(key, value)
            change_strings.append(
                u'{} set to "{}"'.format(prop, val)
            )

        return ', '.join(change_strings)

    @newrelic.agent.function_trace()
    def convert_settings_to_dict(self, old_settings, new_settings, user):
        settings_dict = OrderedDict()
        for field in models.AdGroupSettings._settings_fields:
            if field in ['display_url', 'brand_name', 'description', 'call_to_action'] and\
                    not user.has_perm('zemauth.new_content_ads_tab'):
                continue

            settings_dict[field] = {
                'name': models.AdGroupSettings.get_human_prop_name(field),
                'value': models.AdGroupSettings.get_human_value(field, getattr(
                    new_settings,
                    field,
                    models.AdGroupSettings.get_default_value(field)
                ))
            }

            if old_settings is not None:
                old_value = models.AdGroupSettings.get_human_value(field, getattr(
                    old_settings,
                    field,
                    models.AdGroupSettings.get_default_value(field)
                ))
                settings_dict[field]['old_value'] = old_value

        return settings_dict


class AccountUsers(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'account_access_users_get')
    def get(self, request, account_id):
        if not request.user.has_perm('zemauth.account_agency_access_permissions'):
            raise exc.MissingDataError()

        account = helpers.get_account(request.user, account_id)
        users = [self._get_user_dict(u) for u in account.users.all()]

        return self.create_api_response({
            'users': users
        })

    @statsd_helper.statsd_timer('dash.api', 'account_access_users_put')
    def put(self, request, account_id):
        if not request.user.has_perm('zemauth.account_agency_access_permissions'):
            raise exc.MissingDataError()

        account = helpers.get_account(request.user, account_id)
        resource = json.loads(request.body)

        form = forms.UserForm(resource)
        is_valid = form.is_valid()

        # in case the user already exists and form contains
        # first name and last name, error is returned. In case
        # the form only contains email, user is added to the account.
        if form.cleaned_data.get('email') is None:
            self._raise_validation_error(form.errors)

        first_name = form.cleaned_data.get('first_name')
        last_name = form.cleaned_data.get('last_name')
        email = form.cleaned_data.get('email')

        try:
            user = ZemUser.objects.get(email__iexact=email)

            if (first_name == user.first_name and last_name == user.last_name)\
                    or (not first_name and not last_name):
                created = False
            else:
                self._raise_validation_error(
                    form.errors,
                    message=u'The user with e-mail {} is already registred as \"{}\". Please contact technical support if you want to change the user\'s name or leave first and last names blank if you just want to add access to the account for this user.'.format(user.email, user.get_full_name())
                )
        except ZemUser.DoesNotExist:
            if not is_valid:
                self._raise_validation_error(form.errors)

            user = ZemUser.objects.create_user(email, first_name=first_name, last_name=last_name)

            self._add_user_to_groups(user)
            email_helper.send_email_to_new_user(user, request)

            created = True

        # we check account for this user to prevent multiple additions
        if not len(account.users.filter(pk=user.pk)):
            account.users.add(user)

            # add history entry
            new_settings = account.get_current_settings().copy_settings()
            new_settings.changes_text = u'Added user {} ({})'.format(user.get_full_name(), user.email)
            new_settings.save(request)

        return self.create_api_response(
            {'user': self._get_user_dict(user)},
            status_code=201 if created else 200
        )

    def _raise_validation_error(self, errors, message=None):
        raise exc.ValidationError(
            errors=dict(errors),
            pretty_message=message or u'Please specify the user\'s first name, last name and email.'
        )

    @statsd_helper.statsd_timer('dash.api', 'account_access_users_delete')
    def delete(self, request, account_id, user_id):
        if not request.user.has_perm('zemauth.account_agency_access_permissions'):
            raise exc.MissingDataError()

        account = helpers.get_account(request.user, account_id)

        try:
            user = ZemUser.objects.get(pk=user_id)
        except ZemUser.DoesNotExist:
            raise exc.MissingDataError()

        if len(account.users.filter(pk=user.pk)):
            account.users.remove(user)

            # add history entry
            new_settings = account.get_current_settings().copy_settings()
            new_settings.changes_text = u'Removed user {} ({})'.format(user.get_full_name(), user.email)
            new_settings.save(request)

        return self.create_api_response({
            'user_id': user.id
        })

    def _get_user_dict(self, user):
        return {
            'id': user.id,
            'name': user.get_full_name(),
            'email': user.email,
            'last_login': user.last_login.date(),
            'is_active': user.last_login != user.date_joined,
        }

    def _add_user_to_groups(self, user):
        perm = authmodels.Permission.objects.get(codename='group_new_user_add')
        groups = authmodels.Group.objects.filter(permissions=perm)

        for group in groups:
            group.user_set.add(user)


class UserActivation(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'account_user_activation_mail_post')
    def post(self, request, account_id, user_id):
        if not request.user.has_perm('zemauth.account_agency_access_permissions'):
            raise exc.MissingDataError()

        try:
            user = ZemUser.objects.get(pk=user_id)
            email_helper.send_email_to_new_user(user, request)

            account = helpers.get_account(request.user, account_id)
            # add history entry
            new_settings = account.get_current_settings().copy_settings()
            new_settings.changes_text = u'Resent activation mail {} ({})'.format(user.get_full_name(), user.email)
            new_settings.save(request)

        except ZemUser.DoesNotExist:
            raise exc.ValidationError(
                pretty_message=u'Cannot activate nonexisting user.'
            )

        return self.create_api_response({})
