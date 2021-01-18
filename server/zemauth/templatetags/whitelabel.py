from django import template
from django.db.models import Q

import core.models
import dash.constants

register = template.Library()


def _get_whitelabel_from_host(context=None):
    if not context or "request" not in context:
        return None
    host = context["request"].META.get("HTTP_HOST", "")
    if host == "newscorp.zemanta.com":
        return dash.constants.Whitelabel.NEWSCORP
    if host == "nativeocean.zdsp.io":
        return dash.constants.Whitelabel.DAS
    return None


def _get_user_agencies(context=None):
    if not context or "request" not in context:
        return None
    user = context["request"].user
    if user.is_anonymous:
        return None
    return core.models.agency.Agency.objects.all().filter(
        Q(entitypermission__user__id=user.id) | Q(account__entitypermission__user__id=user.id)
    )


def _get_agency_from_host(context):
    whitelabel = _get_whitelabel_from_host(context)
    if not whitelabel:
        return None
    return core.models.agency.Agency.objects.filter(white_label__theme=whitelabel).all()


@register.simple_tag(takes_context=True)
def whitelabel_from_host(context):
    return _get_whitelabel_from_host(context)


@register.simple_tag(takes_context=True)
def get_whitelabel_info(context):
    info = {
        "base": "zemanta",
        "favicon_url": None,
        "dashboard_title": None,
        "terms_of_service_url": None,
        "copyright_holder": None,
        "copyright_holder_url": None,
    }
    agencies = _get_agency_from_host(context) or _get_user_agencies(context)
    if agencies:
        # As the case of an user with 2 agencies with a whitelabel should be very rare, we decided to take the first one
        # TODO: tfischer 08/03/2019 Have only 1 whitelabel per user. To avoid being on agency B with WL from agency A.
        agencies_w_whitelabel = [agency for agency in agencies if agency.white_label]
        agency = agencies_w_whitelabel[0] if agencies_w_whitelabel else None
        if agency and agency.white_label:
            info["base"] = agency.white_label.theme
            info["favicon_url"] = agency.white_label.favicon_url
            info["dashboard_title"] = agency.white_label.dashboard_title
            info["terms_of_service_url"] = agency.white_label.terms_of_service_url
            info["copyright_holder"] = agency.white_label.copyright_holder
            info["copyright_holder_url"] = agency.white_label.copyright_holder_url
    return info
