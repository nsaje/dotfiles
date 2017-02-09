from decimal import Decimal

from django import forms

from dash import constants

import utils.string_helper


def validate_daily_budget_cc(daily_budget_cc, source_type):
    if daily_budget_cc < 0:
        raise forms.ValidationError('This value must be positive')

    min_daily_budget = source_type.min_daily_budget
    if min_daily_budget is not None and daily_budget_cc < min_daily_budget:
        raise forms.ValidationError('Please provide daily spend cap of at least ${}.'
                                    .format(utils.string_helper.format_decimal(min_daily_budget, 0, 0)))

    max_daily_budget = source_type.max_daily_budget
    if max_daily_budget is not None and daily_budget_cc > max_daily_budget:
        raise forms.ValidationError('Maximum allowed daily spend cap is ${}. If you want use a higher daily spend cap, please contact support.'
                                    .format(utils.string_helper.format_decimal(max_daily_budget, 0, 0)))


def validate_source_cpc_cc(cpc_cc, source, source_type):
    if cpc_cc < 0:
        raise forms.ValidationError('This value must be positive')

    decimal_places = source_type.cpc_decimal_places
    _validate_cpc_decimal_places(cpc_cc, decimal_places, source.name)

    min_cpc = source_type.min_cpc
    _validate_min_cpc(cpc_cc, min_cpc, source.name)

    max_cpc = source_type.max_cpc
    _validate_max_cpc(cpc_cc, max_cpc, source.name)


def validate_ad_group_source_cpc_cc(cpc_cc, ad_group_source):
    ad_group_settings = ad_group_source.ad_group.get_current_settings()

    source_type = ad_group_source.source.source_type
    validate_source_cpc_cc(cpc_cc, ad_group_source.source, source_type)

    min_cpc = source_type.get_min_cpc(ad_group_settings)
    _validate_min_cpc(cpc_cc, min_cpc, ad_group_source.source.name)

    max_cpc = ad_group_settings.cpc_cc
    _validate_max_cpc(cpc_cc, max_cpc, 'ad group')


def validate_b1_sources_group_cpc_cc(cpc_cc, ad_group):
    ad_group_settings = ad_group.get_current_settings()
    if not ad_group_settings.b1_sources_group_enabled:
        return

    if cpc_cc < 0:
        raise forms.ValidationError('RTB Sources\' bid CPC must be positive')

    _validate_cpc_decimal_places(cpc_cc, constants.SourceAllRTB.DECIMAL_PLACES, constants.SourceAllRTB.NAME)
    _validate_min_cpc(cpc_cc, constants.SourceAllRTB.MIN_CPC, constants.SourceAllRTB.NAME)
    _validate_max_cpc(cpc_cc, constants.SourceAllRTB.MAX_CPC, constants.SourceAllRTB.NAME)
    _validate_max_cpc(cpc_cc, ad_group_settings.cpc_cc, 'ad group')


def validate_ad_group_cpc_cc(cpc_cc, ad_group):
    if not cpc_cc:
        return

    ad_group_sources = ad_group.adgroupsource_set.filter(source__deprecated=False, source__maintenance=False)
    sources_with_greater_cpc = []
    for ad_group_source in ad_group_sources:
        settings = ad_group_source.get_current_settings()
        if settings.cpc_cc and settings.cpc_cc > cpc_cc:
            sources_with_greater_cpc.append(ad_group_source.source.name)

    if sources_with_greater_cpc:
        raise forms.ValidationError(
            'Some media sources have higher cpc ({}).'
            .format(", ".join(sources_with_greater_cpc))
        )


def has_too_many_decimal_places(num, decimal_places):
    rounded_num = num.quantize(Decimal('1.{}'.format('0' * decimal_places)))
    return rounded_num != num


def _validate_cpc_decimal_places(cpc_cc, decimal_places, source_name):
    if decimal_places is not None and has_too_many_decimal_places(cpc_cc, decimal_places):
        raise forms.ValidationError(
            'CPC on {} cannot exceed {} decimal place{}.'.format(
                source_name,
                decimal_places,
                's' if decimal_places != 1 else ''))


def _validate_min_cpc(cpc_cc, min_cpc, name):
    if min_cpc is not None and cpc_cc < min_cpc:
        raise forms.ValidationError(
            'Minimum CPC on {} is ${}.'.format(
                name,
                utils.string_helper.format_decimal(min_cpc, 2, 3)
            )
        )


def _validate_max_cpc(cpc_cc, max_cpc, name):
    if max_cpc is not None and cpc_cc > max_cpc:
        raise forms.ValidationError(
            'Maximum CPC on {} is ${}.'.format(
                name,
                utils.string_helper.format_decimal(max_cpc, 2, 3)
            )
        )
