from django import template
from django.db.models import Q

import dash.constants
import core.entity

register = template.Library()


def _get_whitelabel_from_host(context=None):
    if not context or "request" not in context:
        return None
    host = context["request"].META.get("HTTP_HOST", "")
    if host == "newscorp.zemanta.com":
        return dash.constants.Whitelabel.NEWSCORP
    return None


def _get_user_agency(context=None):
    if not context or "request" not in context:
        return None
    user = context["request"].user
    if user.is_anonymous():
        return None
    return core.entity.agency.Agency.objects.all().filter(Q(users__id=user.id) | Q(account__users__id=user.id)).first()


def _get_agency_from_host(context):
    whitelabel = _get_whitelabel_from_host(context)
    if not whitelabel:
        return None
    return core.entity.agency.Agency.objects.filter(whitelabel=whitelabel).first()


@register.simple_tag(takes_context=True)
def whitelabel_from_host(context):
    return _get_whitelabel_from_host(context)


@register.simple_tag(takes_context=True)
def get_whitelabel_info(context):
    info = {"base": "zemanta", "favicon": None, "dashboard_title": None}
    agency = _get_agency_from_host(context) or _get_user_agency(context)
    if agency and agency.whitelabel:
        info["base"] = agency.whitelabel
        info["favicon"] = agency.custom_favicon_url
        info["dashboard_title"] = agency.custom_dashboard_title
    return info
