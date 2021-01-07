# -*- coding: utf-8 -*-

from django.core.exceptions import ValidationError

from core.models.source import Source


def validate_sspd_sources_markets(sources_markets):
    all_sources = set(Source.objects.values_list("name", flat=True))
    form_sources = set(sources_markets.keys())
    invalid_sources = list(form_sources - all_sources)
    if invalid_sources:
        raise ValidationError([{"sspd_sources_markets": "Form contains invalid sources: {}".format(invalid_sources)}])
