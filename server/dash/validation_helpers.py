from decimal import Decimal

from django import forms

import utils.string_helper


def validate_daily_budget_cc(daily_budget_cc, source_type):
    if daily_budget_cc < 0:
        raise forms.ValidationError('This value must be positive')

    min_daily_budget = source_type.min_daily_budget
    if min_daily_budget is not None and daily_budget_cc < min_daily_budget:
        raise forms.ValidationError('Please provide budget of at least ${}.'
                                    .format(utils.string_helper.format_decimal(min_daily_budget, 0, 0)))

    max_daily_budget = source_type.max_daily_budget
    if max_daily_budget is not None and daily_budget_cc > max_daily_budget:
        raise forms.ValidationError('Maximum allowed budget is ${}. If you want use a higher daily budget, please contact support.'
                                    .format(utils.string_helper.format_decimal(max_daily_budget, 0, 0)))


def validate_source_cpc_cc(cpc_cc, source):
    if cpc_cc < 0:
        raise forms.ValidationError('This value must be positive')

    source_type = source.source_type
    decimal_places = source_type.cpc_decimal_places
    if decimal_places is not None and has_too_many_decimal_places(cpc_cc, decimal_places):
        raise forms.ValidationError(
            'CPC on {} cannot exceed {} decimal place{}.'.format(
                source.name, decimal_places, 's' if decimal_places != 1 else ''))

    min_cpc = source_type.min_cpc
    if min_cpc is not None and cpc_cc < min_cpc:
        raise forms.ValidationError(
            'Minimum CPC is ${}.'.format(utils.string_helper.format_decimal(min_cpc, 2, 3)))

    max_cpc = source_type.max_cpc
    if max_cpc is not None and cpc_cc > max_cpc:
        raise forms.ValidationError(
            'Maximum CPC is ${}.'.format(utils.string_helper.format_decimal(max_cpc, 2, 3)))


def validate_ad_group_source_cpc_cc(cpc_cc, ad_group_source):
    validate_source_cpc_cc(cpc_cc, ad_group_source.source)

    ad_group_settings = ad_group_source.ad_group.get_current_settings()
    max_cpc = ad_group_settings.cpc_cc
    if max_cpc is not None and cpc_cc > max_cpc:
        raise forms.ValidationError(
                'Maximum ad group CPC is ${}.'.format(utils.string_helper.format_decimal(max_cpc, 2, 3)))


def validate_ad_group_cpc_cc(cpc_cc, ad_group):
    if not cpc_cc:
        return

    ad_group_sources = ad_group.adgroupsource_set.all()
    sources_with_greater_cpc = []
    for ad_group_source in ad_group_sources:
        settings = ad_group_source.get_current_settings()
        if settings.cpc_cc and settings.cpc_cc > cpc_cc:
            sources_with_greater_cpc.append(ad_group_source.source.name)

    if sources_with_greater_cpc:
        raise forms.ValidationError(
            'Some media sources have grater cpc (${}).'
            .format(", ".join(sources_with_greater_cpc))
        )


def has_too_many_decimal_places(num, decimal_places):
    rounded_num = num.quantize(Decimal('1.{}'.format('0' * decimal_places)))
    return rounded_num != num
