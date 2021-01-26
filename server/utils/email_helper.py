# isort:skip_file
import html
from utils import zlogging
import traceback
import re
from django.db.models import Q
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.core.mail.message import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.template import Context, Template
from urllib.parse import urlparse, urlunparse
from django.http import QueryDict
from typing import Dict, Any

import dash.constants
import dash.models
import zemauth.models

from utils import dates_helper

logger = zlogging.getLogger(__name__)

WHITELABEL_PRODUCTS = {
    dash.constants.Whitelabel.GREENPARK: "Telescope",
    dash.constants.Whitelabel.ADTECHNACITY: "adtechnacity",
    dash.constants.Whitelabel.NEWSCORP: "News Corp",
    dash.constants.Whitelabel.BURDA: "Burda",
    dash.constants.Whitelabel.MEDIAMOND: "Mediamond",
    dash.constants.Whitelabel.ADYOULIKE: "Adyoulike",
    dash.constants.Whitelabel.DAS: "Native Ocean",
}

WHITELABEL_FROM_EMAILS = {dash.constants.Whitelabel.DAS: "info_nativeocean@accelerators.jp"}

URLS_RE = re.compile(
    r"((https?):((//)|(\\\\))+[\w\d:#@%/;$()~_?\+\-=\\\.&]*[\w\d#@%/$()~_\+\-=\\&])", re.MULTILINE | re.UNICODE
)

EMAIL_RE = re.compile(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]*[a-zA-Z0-9])", re.MULTILINE | re.UNICODE)

NO_REPLY_EMAIL = "noreply@zemanta.com"


def send_official_email(
    agency_or_user, recipient_list=None, subject=None, body=None, additional_recipients=None, tags=None, from_email=None
):
    """Sends an official email, meaning it requires an agency or a user to determine
    if the e-mail should be whitelabeled."""
    email = create_official_email(
        agency_or_user=agency_or_user,
        recipient_list=recipient_list,
        subject=subject,
        body=body,
        additional_recipients=additional_recipients,
        tags=tags,
        from_email=from_email,
    )
    _send_email(email)


def create_official_email(
    agency_or_user, recipient_list=None, subject=None, body=None, additional_recipients=None, tags=None, from_email=None
):
    whitelabel = _lookup_whitelabel(agency_or_user)
    if whitelabel:
        subject = _adjust_product_name(whitelabel, subject)
        body = _adjust_product_name(whitelabel, body)
        from_email = WHITELABEL_FROM_EMAILS.get(whitelabel)

    return _create_email(
        whitelabel=whitelabel,
        recipient_list=recipient_list,
        subject=subject,
        body=body,
        additional_recipients=additional_recipients,
        tags=tags,
        from_email=from_email,
    )


def send_internal_email(
    recipient_list=None,
    subject=None,
    body=None,
    additional_recipients=None,
    tags=None,
    from_email=None,
    custom_html=None,
    attachment=None,
):
    email = create_internal_email(
        recipient_list=recipient_list,
        subject=subject,
        body=body,
        additional_recipients=additional_recipients,
        tags=tags,
        from_email=from_email,
        custom_html=custom_html,
    )
    if attachment:
        email.attach(**attachment)
    _send_email(email)


def create_internal_email(
    recipient_list=None,
    subject=None,
    body=None,
    additional_recipients=None,
    tags=None,
    from_email=None,
    custom_html=None,
):
    return _create_email(
        recipient_list=recipient_list,
        subject=subject,
        body=body,
        additional_recipients=additional_recipients,
        tags=tags,
        from_email=from_email,
        custom_html=custom_html,
    )


def _create_email(
    whitelabel=None,
    recipient_list=None,
    subject=None,
    body=None,
    additional_recipients=None,
    tags=None,
    from_email=None,
    custom_html=None,
):
    if not recipient_list and not additional_recipients:
        return
    if not tags:
        tags = ["unclassified"]
    if not from_email:
        from_email = settings.FROM_EMAIL
    if recipient_list is None:
        recipient_list = []

    email = EmailMultiAlternatives(
        subject=html.unescape(subject),
        body=html.unescape(body),
        from_email="{} <{}>".format(WHITELABEL_PRODUCTS.get(whitelabel, "Zemanta"), from_email),
        to=recipient_list,
        bcc=additional_recipients,
        headers={"X-Mailgun-Tag": tags},
    )
    if custom_html:
        email.attach_alternative(custom_html, "text/html")
    else:
        email.attach_alternative(_format_template(subject, body, whitelabel), "text/html")
    return email


def _send_email(email):
    if not settings.EMAIL_HOST and not settings.TESTING:
        return
    email.send()


def params_from_template(template_type, **kwargs) -> Dict[Any, Any]:
    template = dash.models.EmailTemplate.objects.get(template_type=template_type)
    context = Context(kwargs)
    return dict(
        subject=Template(template.subject).render(context),
        body=Template(template.body).render(context),
        additional_recipients=_prepare_recipients(template.recipients),
        tags=[dash.constants.EmailTemplateType.get_name(template_type)],
    )


def _format_template(subject, content, whitelabel=None):
    template_file = "email.html"
    if whitelabel:
        template_file = "whitelabel/{}/email.html".format(whitelabel)
    return render_to_string(template_file, {"subject": subject, "content": _format_whitespace(content)})


def _lookup_whitelabel(agency_or_user):
    if not agency_or_user:
        return None

    agency = None
    if isinstance(agency_or_user, dash.models.Agency):
        agency = agency_or_user
    elif isinstance(agency_or_user, zemauth.models.User):
        user = agency_or_user
        agency = (
            dash.models.Agency.objects.all()
            .filter(Q(entitypermission__user__id=user.id) | Q(account__entitypermission__user__id=user.id))
            .first()
        )
    else:
        raise Exception("Incorrect agency or user for whitelabel purposes!")

    if agency:
        return agency.white_label.theme if agency.white_label else ""
    return None


def _adjust_product_name(whitelabel, text):
    if whitelabel not in WHITELABEL_PRODUCTS:
        return text
    new_product_name = WHITELABEL_PRODUCTS[whitelabel]
    return text.replace("Zemanta One", new_product_name).replace("Zemanta", new_product_name)


def _url_to_link(text):
    return URLS_RE.sub(r'<a href="\1" target="_blank">\1</a>', text)


def _email_to_link(text):
    return EMAIL_RE.sub(r'<a href="mailto:\1">\1</a>', text)


def _bold(text, bold):
    return text.replace(bold, "<b>" + bold + "</b>")


def _prepare_recipients(email_text):
    return [email.strip() for email in email_text.split(",") if email]


def _format_whitespace(content):
    """
    Format multiple concurrent new line characters into paragraphs and single new lines into line breaks.
    """
    content = re.sub(r"\n\n+", "</p><p>", content)
    content = re.sub(r"\n", "<br>", content)
    return "<p>{}</p>".format(content)


def email_manager_list(campaign):
    """
    Fetch campaign manager email if it exists
    """
    campaign_manager = campaign.settings.campaign_manager
    ret = set([])
    if campaign_manager is not None:
        ret.add(campaign_manager.email)
    return sorted(ret)


def send_obj_changes_notification_email(obj, request, changes_text):
    if isinstance(obj, dash.models.AdGroup):
        send_ad_group_notification_email(obj, request, changes_text)
    elif isinstance(obj, dash.models.Campaign):
        send_campaign_notification_email(obj, request, changes_text)
    elif isinstance(obj, dash.models.Account):
        send_account_notification_email(obj, request, changes_text)
    else:
        raise Exception("Object {} (pk: {}) does not have a notification email method set".format(obj, obj.pk))


def send_ad_group_notification_email(ad_group, request, changes_text):
    if not should_send_notification_mail(ad_group.campaign, request.user, request):
        return

    link_url = request.build_absolute_uri("/v2/analytics/adgroup/{}?history".format(ad_group.pk))
    link_url = link_url.replace("http://", "https://")
    args = {
        "user": request.user,
        "ad_group": ad_group,
        "campaign": ad_group.campaign,
        "account": ad_group.campaign.account,
        "link_url": link_url,
        "changes_text": _format_changes_text(changes_text),
    }

    emails = list(set(email_manager_list(ad_group.campaign)) - set([request.user.email]))
    if not emails:
        return
    send_official_email(
        agency_or_user=ad_group.campaign.account.agency,
        recipient_list=emails,
        **params_from_template(dash.constants.EmailTemplateType.ADGROUP_CHANGE, **args),
    )


def send_campaign_notification_email(campaign, request, changes_text):
    if not should_send_notification_mail(campaign, request.user, request):
        return

    link_url = request.build_absolute_uri("/v2/analytics/campaign/{}?history".format(campaign.pk))
    link_url = link_url.replace("http://", "https://")

    args = {
        "user": request.user,
        "campaign": campaign,
        "account": campaign.account,
        "link_url": link_url,
        "changes_text": _format_changes_text(changes_text),
    }

    emails = list(set(email_manager_list(campaign)) - set([request.user.email]))
    if not emails:
        return
    send_official_email(
        agency_or_user=campaign.account.agency,
        recipient_list=emails,
        **params_from_template(dash.constants.EmailTemplateType.CAMPAIGN_CHANGE, **args),
    )


def send_account_notification_email(account, request, changes_text):
    if not should_send_account_notification_mail(account, request.user, request):
        return

    link_url = request.build_absolute_uri("/v2/analytics/account/{}?history".format(account.pk))
    link_url = link_url.replace("http://", "https://")

    args = {
        "user": request.user,
        "account": account,
        "link_url": link_url,
        "changes_text": _format_changes_text(changes_text),
    }

    send_official_email(
        agency_or_user=account.agency,
        recipient_list=[account.get_current_settings().default_account_manager.email],
        **params_from_template(dash.constants.EmailTemplateType.ACCOUNT_CHANGE, **args),
    )


def send_account_pixel_notification(account, request):
    if not should_send_account_notification_mail(account, request.user, request):
        return
    link_url = request.build_absolute_uri("/v2/analytics/account/{}?settings".format(account.pk))
    link_url = link_url.replace("http://", "https://")
    args = {"user": request.user, "account": account, "link_url": link_url}
    account_settings = account.get_current_settings()

    send_official_email(
        agency_or_user=account.agency,
        recipient_list=[account_settings.default_account_manager.email],
        **params_from_template(dash.constants.EmailTemplateType.PIXEL_ADD, **args),
    )


def send_password_reset_email(user, request, next_param=""):
    args = {"user": user, "link_url": _generate_password_reset_url(user, request, next_param)}

    send_official_email(
        agency_or_user=user,
        recipient_list=[user.email],
        **params_from_template(dash.constants.EmailTemplateType.PASSWORD_RESET, **args),
    )


def send_new_user_email(user, request):
    args = {"user": user, "link_url": _generate_new_user_url(user, request)}
    send_official_email(
        agency_or_user=user,
        recipient_list=[user.email],
        **params_from_template(dash.constants.EmailTemplateType.USER_NEW, **args),
    )


def _generate_new_user_url(user, request):
    encoded_id = urlsafe_base64_encode(str(user.pk).encode("utf-8"))
    token = default_token_generator.make_token(user)

    url = request.build_absolute_uri(reverse("welcome", args=(encoded_id, token)))
    url_parts = list(urlparse(url))
    return urlunparse(url_parts).replace("http://", "https://")


def _generate_password_reset_url(user, request, next_param=""):
    encoded_id = urlsafe_base64_encode(str(user.pk).encode("utf-8"))
    token = default_token_generator.make_token(user)

    url = request.build_absolute_uri(reverse("set_password", args=(encoded_id, token)))
    url_parts = list(urlparse(url))
    if next_param:
        querystring = QueryDict(url_parts[4], mutable=True)
        querystring["next"] = next_param
        url_parts[4] = querystring.urlencode(safe="/")
    return urlunparse(url_parts).replace("http://", "https://")


def send_supply_report_email(
    email,
    date,
    impressions,
    cost,
    custom_subject=None,
    publisher_report=None,
    mtd_impressions=None,
    mtd_cost=None,
    daily_breakdown_report=None,
):
    date = dates_helper.format_date_mmddyyyy(date)
    args = {
        "date": date,
        "impressions": impressions,
        "cost": cost,
        "mtd_impressions": mtd_impressions,
        "mtd_cost": mtd_cost,
    }
    params = params_from_template(dash.constants.EmailTemplateType.SUPPLY_REPORT, **args)
    if custom_subject:
        params["subject"] = custom_subject.format(date=date)

    try:
        email = create_official_email(
            None, recipient_list=[email], from_email=settings.SUPPLY_REPORTS_FROM_EMAIL, **params
        )
        if publisher_report:
            email.attach("publisher_report.csv", publisher_report, "text/csv")

        if daily_breakdown_report is not None:
            email.attach("month_to_date_report.csv", daily_breakdown_report, "text/csv")

        _send_email(email)
    except Exception:
        logger.error(
            "Supply report e-mail to %s was not sent because an exception was raised: %s", email, traceback.format_exc()
        )


def should_send_account_notification_mail(account, user, request):
    if not settings.SEND_NOTIFICATION_MAIL:
        return False

    account_settings = account.get_current_settings()

    if not account_settings or not account_settings.default_account_manager:
        logger.error(
            "Could not send e-mail because there is no default account " "manager set for account with id %s.",
            account.pk,
        )
        return False

    if user.pk == account_settings.default_account_manager.pk:
        return False

    return True


def should_send_notification_mail(campaign, user, request):
    if not settings.SEND_NOTIFICATION_MAIL:
        return False
    if getattr(request, "is_api_request", False):
        return False

    campaign_settings = campaign.get_current_settings()

    if not campaign_settings or not campaign_settings.campaign_manager:
        logger.error(
            "Could not send e-mail because there is no account manager " "set for campaign with id %s.", campaign.pk
        )
        return False

    if user.pk == campaign_settings.campaign_manager.pk:
        return False

    return True


def send_new_user_device_email(request, browser, os, city, country):
    send_official_email(
        agency_or_user=request.user,
        recipient_list=[request.user.email],
        **params_from_template(
            dash.constants.EmailTemplateType.NEW_DEVICE_LOGIN,
            time=dates_helper.local_now().strftime("%A, %d %b %Y %I:%m %p %Z"),
            browser=browser,
            os=os,
            city=city,
            country=country,
            reset_password_url=request.build_absolute_uri(("password_reset")),
        ),
    )


def send_ga_setup_instructions(user):
    send_official_email(
        agency_or_user=user,
        recipient_list=[user.email],
        **params_from_template(dash.constants.EmailTemplateType.GA_SETUP_INSTRUCTIONS),
    )


def _format_report_filters(show_archived, show_blacklisted_publishers, filtered_sources):
    filters = []
    if show_archived:
        filters.append("Show archived items")
    if show_blacklisted_publishers != dash.constants.PublisherBlacklistFilter.SHOW_ALL:
        filters.append(
            "Show {} publishers only".format(
                dash.constants.PublisherBlacklistFilter.get_text(show_blacklisted_publishers).lower()
            )
        )
    if filtered_sources:
        filters.extend([x.name for x in filtered_sources])
    return filters


def send_async_report(
    user,
    recipients,
    report_path,
    start_date,
    end_date,
    expiry_date,
    filtered_sources,
    show_archived,
    show_blacklisted_publishers,
    view,
    breakdowns,
    columns,
    include_totals,
    ad_group_name,
    campaign_name,
    account_name,
    **kwargs,
):

    filters = _format_report_filters(show_archived, show_blacklisted_publishers, filtered_sources)

    send_official_email(
        agency_or_user=user,
        recipient_list=recipients,
        **params_from_template(
            dash.constants.EmailTemplateType.ASYNC_REPORT_RESULTS,
            link_url=report_path,
            account_name=account_name or "/",
            campaign_name=campaign_name or "/",
            ad_group_name=ad_group_name or "/",
            start_date=dates_helper.format_date_mmddyyyy(start_date),
            end_date=dates_helper.format_date_mmddyyyy(end_date),
            expiry_date=dates_helper.format_date_mmddyyyy(expiry_date),
            tab_name=view,
            breakdown=", ".join(breakdowns) or "/",
            columns=", ".join(columns),
            filters=", ".join(filters) if filters else "/",
            include_totals="Yes" if include_totals else "No",
            reprocess_title_prefix=kwargs.get("reprocess_title_prefix", ""),
            reprocess_reason=kwargs.get("reprocess_reason", ""),
        ),
    )


def send_async_report_fail(
    user,
    recipients,
    start_date,
    end_date,
    filtered_sources,
    show_archived,
    show_blacklisted_publishers,
    view,
    breakdowns,
    columns,
    include_totals,
    ad_group_name,
    campaign_name,
    account_name,
):

    filters = _format_report_filters(show_archived, show_blacklisted_publishers, filtered_sources)

    send_official_email(
        agency_or_user=user,
        recipient_list=recipients,
        **params_from_template(
            dash.constants.EmailTemplateType.ASYNC_REPORT_FAIL,
            account_name=account_name or "/",
            campaign_name=campaign_name or "/",
            ad_group_name=ad_group_name or "/",
            start_date=dates_helper.format_date_mmddyyyy(start_date),
            end_date=dates_helper.format_date_mmddyyyy(end_date),
            tab_name=view,
            breakdown=", ".join(breakdowns) or "/",
            columns=", ".join(columns),
            filters=", ".join(filters) if filters else "/",
            include_totals="Yes" if include_totals else "No",
        ),
    )


def send_async_scheduled_report(
    user,
    recipients,
    report_name,
    frequency,
    report_path,
    expiry_date,
    start_date,
    end_date,
    filtered_sources,
    show_archived,
    show_blacklisted_publishers,
    include_totals,
    view,
    breakdowns,
    columns,
    ad_group_name,
    campaign_name,
    account_name,
    **kwargs,
):

    filters = _format_report_filters(show_archived, show_blacklisted_publishers, filtered_sources)

    send_official_email(
        agency_or_user=user,
        recipient_list=recipients,
        from_email=NO_REPLY_EMAIL,
        **params_from_template(
            dash.constants.EmailTemplateType.ASYNC_SCHEDULED_REPORT_RESULTS,
            report_name=report_name,
            frequency=frequency.lower(),
            cancel_url="https://one.zemanta.com/v2/reports/accounts",
            link_url=report_path,
            account_name=account_name or "/",
            campaign_name=campaign_name or "/",
            ad_group_name=ad_group_name or "/",
            start_date=dates_helper.format_date_mmddyyyy(start_date),
            end_date=dates_helper.format_date_mmddyyyy(end_date),
            expiry_date=dates_helper.format_date_mmddyyyy(expiry_date),
            tab_name=view,
            breakdown=", ".join(breakdowns) or "/",
            columns=", ".join(columns),
            filters=", ".join(filters) if filters else "/",
            include_totals="Yes" if include_totals else "No",
            reprocess_title_prefix=kwargs.get("reprocess_title_prefix", ""),
            reprocess_reason=kwargs.get("reprocess_reason", ""),
        ),
    )


def send_depleting_credits_email(user, accounts):
    accounts_list = ""
    for account in accounts:
        accounts_list += " - {} {}\n".format(
            account.get_long_name(), "https://one.zemanta.com/v2/credit/account/{}".format(account.pk)
        )

    send_official_email(
        recipient_list=[user.email],
        agency_or_user=user,
        **params_from_template(dash.constants.EmailTemplateType.DEPLETING_CREDITS, accounts_list=accounts_list),
    )


def _format_changes_text(changes_text):
    lines = changes_text.split("\n")
    for i in range(len(lines)):
        lines[i] = "- " + lines[i]

        # remove end punctuations
        if lines[i][-1] in ".,":
            lines[i] = lines[i][:-1]

        # append the right punctuation
        lines[i] += "." if (i + 1) == len(lines) else ","

    return "\n".join(lines)


def send_oen_postclickkpi_cpa_factors_email(factors):
    try:
        email = create_internal_email(
            **params_from_template(dash.constants.EmailTemplateType.OEN_POSTCLICKKPI_CPA_FACTORS)
        )
        email.attach("cpa_optimization_factors.csv", factors, "text/csv")
        _send_email(email)
    except Exception:
        logger.error(
            "OEN CPA Optimization factors e-mail was not sent because an exception was raised: %s",
            traceback.format_exc(),
        )


def send_restapi_access_enabled_notification(user):
    send_official_email(
        agency_or_user=user,
        recipient_list=[user.email],
        **params_from_template(dash.constants.EmailTemplateType.USER_ENABLE_RESTAPI, user=user),
    )


def send_campaign_created_email(request, campaign):
    if not settings.SEND_NOTIFICATION_MAIL:
        return
    if not request:
        return

    agency_url = None
    if campaign.account.agency_id:
        agency_url = request.build_absolute_uri(
            "/v2/analytics/accounts?filtered_agencies={}".format(campaign.account.agency_id)
        )
        agency_url = agency_url.replace("http://", "https://")
    account_url = request.build_absolute_uri("/v2/analytics/account/{}".format(campaign.account_id))
    account_url = account_url.replace("http://", "https://")
    campaign_url = request.build_absolute_uri("/v2/analytics/campaign/{}".format(campaign.id))
    campaign_url = campaign_url.replace("http://", "https://")

    args = {
        "account": campaign.account,
        "campaign_url": campaign_url,
        "account_url": account_url,
        "agency_url": agency_url,
    }

    emails = []
    if campaign.account.settings.default_sales_representative:
        emails.append(campaign.account.settings.default_sales_representative.email)
    if campaign.account.settings.default_cs_representative:
        emails.append(campaign.account.settings.default_cs_representative.email)
    if campaign.account.settings.ob_sales_representative:
        emails.append(campaign.account.settings.ob_sales_representative.email)
    if campaign.account.settings.ob_account_manager:
        emails.append(campaign.account.settings.ob_account_manager.email)
    try:
        emails.remove(request.user.email)
    except ValueError:
        pass
    if not emails:
        return

    send_official_email(
        agency_or_user=campaign.account.agency,
        recipient_list=emails,
        **params_from_template(dash.constants.EmailTemplateType.CAMPAIGN_CREATED, **args),
    )


def send_campaign_cloned_success_email(request, source_campaign_name, cloned_campaign_name):

    args = {"source_campaign_name": source_campaign_name, "cloned_campaign_name": cloned_campaign_name}

    send_official_email(
        agency_or_user=request.user,
        recipient_list=[request.user.email],
        **params_from_template(dash.constants.EmailTemplateType.CAMPAIGN_CLONED_SUCCESS, **args),
    )


def send_campaign_cloned_error_email(request, source_campaign_name, cloned_campaign_name, error_message=None):

    args = {
        "source_campaign_name": source_campaign_name,
        "cloned_campaign_name": cloned_campaign_name,
        "error_message": error_message,
    }

    send_official_email(
        agency_or_user=request.user,
        recipient_list=[request.user.email],
        **params_from_template(dash.constants.EmailTemplateType.CAMPAIGN_CLONED_ERROR, **args),
    )


def send_ad_group_cloned_success_email(request, source_ad_group_name, cloned_ad_group_name):

    args = {"source_ad_group_name": source_ad_group_name, "cloned_ad_group_name": cloned_ad_group_name}

    send_official_email(
        agency_or_user=request.user,
        recipient_list=[request.user.email],
        **params_from_template(dash.constants.EmailTemplateType.AD_GROUP_CLONED_SUCCESS, **args),
    )


def send_ad_group_cloned_error_email(request, source_ad_group_name, cloned_ad_group_name, error_message=None):

    args = {
        "source_ad_group_name": source_ad_group_name,
        "cloned_ad_group_name": cloned_ad_group_name,
        "error_message": error_message,
    }

    send_official_email(
        agency_or_user=request.user,
        recipient_list=[request.user.email],
        **params_from_template(dash.constants.EmailTemplateType.AD_GROUP_CLONED_ERROR, **args),
    )


def send_unknown_sales_office_email(sales_office):

    args = {"sales_office": sales_office}

    send_internal_email(**params_from_template(dash.constants.EmailTemplateType.UNKNOWN_SALES_OFFICE, **args))
