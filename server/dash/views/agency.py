import json
import logging
import traceback
import datetime

import actionlog.api

from collections import OrderedDict
from decimal import Decimal
from django.db import transaction
from django.conf import settings
from django.core.mail import send_mail
from django.core.urlresolvers import reverse

from . import helpers

from dash import forms
from dash import models
from dash import api
from dash import budget
from dash import constants
from utils import api_common
from utils import statsd_helper
from utils import exc
from utils import pagerduty_helper

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

    recipients = [campaign_settings[0].account_manager.email]

    subject = u'Settings change - ad group {}, campaign {}, account {}'.format(
        ad_group.name,
        ad_group.campaign.name,
        ad_group.campaign.account.name
    )

    link_url = request.build_absolute_uri('/ad_groups/{}/agency'.format(ad_group.pk))
    link_url = link_url.replace('http://', 'https://')

    body = u'''Hi account manager of {ad_group.name}

We'd like to notify you that {user.email} has made a change in the settings of the ad group {ad_group.name}, campaign {campaign.name}, account {account.name}. Please check {link_url} for details.

Yours truly,
Zemanta
    '''
    body = body.format(
        user=user,
        ad_group=ad_group,
        campaign=ad_group.campaign,
        account=ad_group.campaign.account,
        link_url=link_url
    )

    try:
        send_mail(
            subject,
            body,
            settings.AD_GROUP_SETTINGS_CHANGE_FROM_EMAIL,
            recipients,
            fail_silently=False
        )
    except Exception as e:
        logger.error('E-mail notification for ad group settings (ad group id: %d) change was not sent because an exception was raised: %s', ad_group.pk, traceback.format_exc(e))

        desc = {
            'campaign_settings_url': get_campaign_url(ad_group, request)
        }
        pagerduty_helper.trigger(
            event_type=pagerduty_helper.PagerDutyEventType.SYSOPS,
            incident_key='ad_group_settings_change_mail_failed',
            description='E-mail notification for ad group settings change was not sent because an exception was raised: {}'.format(traceback.format_exc(e)),
            details=desc,
        )


class AdGroupSettings(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_settings_get')
    def get(self, request, ad_group_id):
        if not request.user.has_perm('dash.settings_view'):
            raise exc.MissingDataError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        settings = self.get_current_settings(ad_group)

        response = {
            'settings': self.get_dict(settings, ad_group),
            'action_is_waiting': actionlog.api.is_waiting_for_set_actions(ad_group)
        }

        return self.create_api_response(response)

    @statsd_helper.statsd_timer('dash.api', 'ad_group_settings_put')
    def put(self, request, ad_group_id):
        if not request.user.has_perm('dash.settings_view'):
            raise exc.MissingDataError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id, select_related=True)

        current_settings = self.get_current_settings(ad_group)

        resource = json.loads(request.body)

        form = forms.AdGroupSettingsForm(
            current_settings, resource.get('settings', {})
            # initial=current_settings
        )
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        self.set_ad_group(ad_group, form.cleaned_data)

        settings = models.AdGroupSettings()
        self.set_settings(settings, current_settings, ad_group, form.cleaned_data)

        with transaction.atomic():
            ad_group.save()
            settings.save()

        api.order_ad_group_settings_update(ad_group, current_settings, settings)

        user = request.user
        changes = current_settings.get_setting_changes(settings)
        if changes:
            send_ad_group_settings_change_mail_if_necessary(ad_group, user, request)

        response = {
            'settings': self.get_dict(settings, ad_group),
            'action_is_waiting': actionlog.api.is_waiting_for_set_actions(ad_group)
        }

        return self.create_api_response(response)

    def get_current_settings(self, ad_group):
        settings = models.AdGroupSettings.objects.\
            filter(ad_group=ad_group).\
            order_by('-created_dt')
        if settings:
            settings = settings[0]
        else:
            settings = models.AdGroupSettings(
                state=constants.AdGroupSettingsState.INACTIVE,
                start_date=datetime.datetime.utcnow().date(),
                cpc_cc=0.4000,
                daily_budget_cc=10.0000,
                target_devices=constants.AdTargetDevice.get_all()
            )

        return settings

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
                'tracking_code': settings.tracking_code
            }

        return result

    def set_ad_group(self, ad_group, resource):
        ad_group.name = resource['name']

    def set_settings(self, settings, current_settings, ad_group, resource):
        settings.ad_group = ad_group
        settings.state = resource['state']
        settings.start_date = resource['start_date']
        settings.end_date = resource['end_date']
        settings.cpc_cc = resource['cpc_cc']
        settings.daily_budget_cc = resource['daily_budget_cc']
        settings.target_devices = resource['target_devices']
        settings.target_regions = resource['target_regions']
        settings.tracking_code = current_settings.tracking_code


class CampaignSettings(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'campaign_settings_get')
    def get(self, request, campaign_id):
        if not request.user.has_perm('zemauth.campaign_settings_view'):
            raise exc.MissingDataError()

        campaign = helpers.get_campaign(request.user, campaign_id)

        campaign_settings = self.get_current_settings(campaign)

        response = {
            'settings': self.get_dict(campaign_settings, campaign),
            'account_managers': self.get_user_list(campaign_settings, 'campaign_settings_account_manager'),
            'sales_reps': self.get_user_list(campaign_settings, 'campaign_settings_sales_rep'),
            'history': self.get_history(campaign)
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

        with transaction.atomic():
            campaign.save()
            settings.save()

        response = {
            'settings': self.get_dict(settings, campaign),
            'history': self.get_history(campaign)
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
            })
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

    def get_current_settings(self, campaign):
        settings = models.CampaignSettings.objects.\
            filter(campaign=campaign).\
            order_by('-created_dt')
        if settings:
            settings = settings[0]
        else:
            settings = models.CampaignSettings()

        return settings

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
            allocate_amount=form.cleaned_data['allocate'],
            revoke_amount=form.cleaned_data['revoke'],
            user=request.user,
            comment=form.cleaned_data['comment'],
            latest_id=budget_change['latest_id']
        )

        response = self.get_response(campaign)

        return self.create_api_response(response)

    def get_response(self, campaign):
        campaign_budget = budget.CampaignBudget(campaign)

        total = campaign_budget.get_total()
        spend = campaign_budget.get_spend()
        available = total - spend

        response = {
            'latest_id': campaign_budget.get_latest_id(),
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
            item['datetime'] = h.created_dt.isoformat()
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

        return self.create_api_response(self.get_response(account))

    @statsd_helper.statsd_timer('dash.api', 'account_agency_put')
    def put(self, request, account_id):
        if not request.user.has_perm('zemauth.account_agency_view'):
            raise exc.MissingDataError()

        account = helpers.get_account(request.user, account_id)

        resource = json.loads(request.body)

        form = forms.AccountAgencySettingsForm(resource.get('settings', {}))
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        account.name = form.cleaned_data['name']
        account.save()

        return self.create_api_response(self.get_response(account))

    def get_response(self, data):
        return {
            'settings': {
                'id': data.id,
                'name': data.name
            }
        }


class AdGroupAgency(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_agency_get')
    def get(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.ad_group_agency_tab_view'):
            raise exc.MissingDataError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        settings = self.get_current_settings(ad_group)

        response = {
            'settings': self.get_dict(settings, ad_group),
            'action_is_waiting': actionlog.api.is_waiting_for_set_actions(ad_group),
            'history': self.get_history(ad_group)
        }

        return self.create_api_response(response)

    @statsd_helper.statsd_timer('dash.api', 'ad_group_settings_put')
    def put(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.ad_group_agency_tab_view'):
            raise exc.MissingDataError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        current_settings = self.get_current_settings(ad_group)

        resource = json.loads(request.body)

        form = forms.AdGroupAgencySettingsForm(resource.get('settings', {}))
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        settings = models.AdGroupSettings()
        self.set_settings(settings, current_settings, ad_group, form.cleaned_data)

        with transaction.atomic():
            settings.save()

        api.order_ad_group_settings_update(ad_group, current_settings, settings)

        user = request.user
        changes = current_settings.get_setting_changes(settings)
        if changes:
            send_ad_group_settings_change_mail_if_necessary(ad_group, user, request)

        response = {
            'settings': self.get_dict(settings, ad_group),
            'action_is_waiting': actionlog.api.is_waiting_for_set_actions(ad_group),
            'history': self.get_history(ad_group)
        }

        return self.create_api_response(response)

    def get_current_settings(self, ad_group):
        settings = models.AdGroupSettings.objects.\
            filter(ad_group=ad_group).\
            order_by('-created_dt')
        if settings:
            settings = settings[0]
        else:
            settings = models.AdGroupSettings()

        return settings

    def get_dict(self, settings, ad_group):
        result = {}

        if settings:
            result = {
                'id': str(ad_group.pk),
                'tracking_code': settings.tracking_code
            }

        return result

    def set_settings(self, settings, current_settings, ad_group, resource):
        settings.ad_group = ad_group
        settings.state = current_settings.state
        settings.start_date = current_settings.start_date
        settings.end_date = current_settings.end_date
        settings.cpc_cc = current_settings.cpc_cc
        settings.daily_budget_cc = current_settings.daily_budget_cc
        settings.target_devices = current_settings.target_devices
        settings.target_regions = current_settings.target_regions
        settings.tracking_code = resource['tracking_code']

    def get_history(self, ad_group):
        settings = models.AdGroupSettings.objects.\
            filter(ad_group=ad_group).\
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
                'changes_text': self.convert_changes_to_string(changes),
                'settings': settings_dict.values(),
                'show_old_settings': old_settings is not None
            })

        return history

    def convert_changes_to_string(self, changes):
        if changes is None:
            return 'Created settings'

        change_strings = []

        for key, value in changes.iteritems():
            prop = models.AdGroupSettings.get_human_prop_name(key)
            val = models.AdGroupSettings.get_human_value(key, value)
            change_strings.append(
                '{} set to "{}"'.format(prop, val)
            )

        return ', '.join(change_strings)

    def convert_settings_to_dict(self, old_settings, new_settings):
        settings_dict = OrderedDict()
        for field in models.AdGroupSettings._settings_fields:
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


