import json
import os

import requests

CREDITS_URL = "/rest/v1/accounts/%s/credits/"
BUDGETS_URL = "/rest/v1/campaigns/%s/budgets/"
CAMPAIGNS_URL = "/rest/v1/campaigns/"
ADGROUPS_URL = "/rest/v1/adgroups/"
ADGROUP_SOURCES = "/rest/v1/adgroups/%s/sources/"
ADGROUP_REALTIMESTATS = "/rest/v1/adgroups/%s/realtimestats/"
REALTIMESTATS_URL = "/rest/v1/realtimestats/%s"
ALLRTB_SOURCES = "/rest/v1/adgroups/%s/sources/rtb/"
REPORTS_URL = "/rest/v1/reports/"
CONTENTADS_URL = "/rest/v1/contentads/?adGroupId=%s"
CONTENTADS_UPLOAD_URL = "/rest/v1/contentads/batch/?adGroupId=%s"
CONTENTADS_BATCH_STATUS_URL = "/rest/v1/contentads/batch/%s"
PUBLISHERS_URL = "/rest/v1/adgroups/%s/publishers/"
PUBLISHER_GROUPS_URL = "/rest/v1/accounts/%s/publishergroups/"
BULK_UPLOAD_URL = "/rest/beta/bulkupload/"
BOOKS_CLOSED_URL = "/rest/v1/booksclosed/"


_token = None
_session = None
_profile = None
_profiles = {}

_script_dir = os.path.dirname(os.path.abspath(__file__))
try:
    with open(os.path.join(_script_dir, ".z1profiles"), "r") as profiles_file:
        _profiles = json.load(profiles_file)
except FileNotFoundError:
    print("ERROR: Please copy the .z1profiles.example file into .z1profiles before using this client.")


def set_profile(profile_name):
    global _profile, _token, _session
    if not _profiles:
        return
    if profile_name not in _profiles:
        raise Exception("Profile '%s' doesn't exist!" % profile_name)
    _profile = _profiles.get(profile_name)
    _token = None
    _session = None


def profile_get(key):
    if key not in _profile:
        raise Exception("Key '%s' doesn't exist in profile" % key)
    return _profile.get(key)


set_profile(os.environ.get("Z1_PROFILE", "default"))


def get_base_url():
    return profile_get("base_url")


def get_token():
    global _token
    if _token:
        return _token
    r = requests.post(
        get_base_url() + "/o/token/",
        auth=(profile_get("client_id"), profile_get("client_secret")),
        data={"grant_type": "client_credentials"},
    )
    if r.status_code != 200:
        raise Exception("Authentication invalid: %s", r.text)
    _token = _try_json(r)["access_token"]
    return _token


def get_session():
    global _session
    if _session:
        return _session
    _session = requests.Session()
    _session.headers.update({"Authorization": "Bearer %s" % get_token()})
    return _session


def _try_json(response):
    try:
        return response.json()
    except Exception:
        return response


# credits


def list_credits(account_id=None):
    r = get_session().get((get_base_url() + CREDITS_URL) % account_id)
    return _try_json(r)


# budgets


def list_budgets(campaign_id):
    r = get_session().get((get_base_url() + BUDGETS_URL) % campaign_id)
    return _try_json(r)


def create_budget(campaign_id, data):
    r = get_session().post((get_base_url() + BUDGETS_URL) % campaign_id, json=data)
    return _try_json(r)


# campaigns


def list_campaigns(account_id=None):
    params = {"accountId": account_id} if account_id else None
    r = get_session().get(get_base_url() + CAMPAIGNS_URL, params=params)
    return _try_json(r)


def create_campaign(data):
    r = get_session().post(get_base_url() + CAMPAIGNS_URL, json=data)
    return _try_json(r)


def get_campaign(campaign_id):
    r = get_session().get(get_base_url() + CAMPAIGNS_URL + str(campaign_id))
    return _try_json(r)


def update_campaign(campaign_id, data):
    r = get_session().put(get_base_url() + CAMPAIGNS_URL + str(campaign_id), json=data)
    return _try_json(r)


def get_campaign_stats(campaign_id, str_date_from, str_date_to):
    r = get_session().get(
        get_base_url() + CAMPAIGNS_URL + str(campaign_id) + "/stats/?from=%s&to=%s" % (str_date_from, str_date_to)
    )
    return _try_json(r)


# ad groups


def list_adgroups(campaign_id=None):
    params = {"campaignId": campaign_id} if campaign_id else None
    r = get_session().get(get_base_url() + ADGROUPS_URL, params=params)
    return _try_json(r)


def create_adgroup(data):
    r = get_session().post(get_base_url() + ADGROUPS_URL, json=data)
    return _try_json(r)


def get_adgroup(adgroup_id):
    r = get_session().get(get_base_url() + ADGROUPS_URL + str(adgroup_id))
    return _try_json(r)


def update_adgroup(adgroup_id, data):
    r = get_session().put(get_base_url() + ADGROUPS_URL + str(adgroup_id), json=data)
    return _try_json(r)


# ad group sources


def get_adgroup_realtimestats(adgroup_id):
    r = get_session().get((get_base_url() + ADGROUP_REALTIMESTATS) % adgroup_id)
    return _try_json(r)


# realtimestats


def get_realtimestats(
    top=False,
    breakdown=None,
    limit=None,
    marker=None,
    account_id=None,
    campaign_id=None,
    ad_group_id=None,
    content_ad_id=None,
):
    params = {
        "breakdown": breakdown,
        "account_id": account_id,
        "campaign_id": campaign_id,
        "ad_group_id": ad_group_id,
        "content_ad_id": content_ad_id,
        "limit": limit,
        "marker": marker,
    }
    url = (get_base_url() + REALTIMESTATS_URL) % ("top/" if top else "",)
    r = get_session().get(url, params=params)
    return _try_json(r)


# ad group sources


def get_adgroup_sources(adgroup_id):
    r = get_session().get((get_base_url() + ADGROUP_SOURCES) % adgroup_id)
    return _try_json(r)


def update_adgroup_sources(adgroup_id, data):
    r = get_session().put((get_base_url() + ADGROUP_SOURCES) % adgroup_id, json=data)
    return _try_json(r)


# all RTB settings


def get_adgroup_sources_rtb(adgroup_id):
    r = get_session().get((get_base_url() + ALLRTB_SOURCES) % adgroup_id)
    return _try_json(r)


def update_adgroup_sources_rtb(adgroup_id, data):
    r = get_session().put((get_base_url() + ALLRTB_SOURCES) % adgroup_id, json=data)
    return _try_json(r)


# reports


def create_report_job(data):
    r = get_session().post((get_base_url() + REPORTS_URL), json=data)
    return _try_json(r)


def get_report_job(job_id):
    r = get_session().get((get_base_url() + REPORTS_URL) + str(job_id))
    return _try_json(r)


# content ads


def list_contentads(adgroup_id):
    r = get_session().get((get_base_url() + CONTENTADS_URL) % adgroup_id)
    return _try_json(r)


def upload_contentads(adgroup_id, data):
    r = get_session().post((get_base_url() + CONTENTADS_UPLOAD_URL) % adgroup_id, json=data)
    return _try_json(r)


def get_contentads_batch_status(batch_id):
    r = get_session().get((get_base_url() + CONTENTADS_BATCH_STATUS_URL) % batch_id)
    return _try_json(r)


# publishers


def get_publishers(adgroup_id):
    r = get_session().get((get_base_url() + PUBLISHERS_URL) % adgroup_id)
    return _try_json(r)


def update_publishers(adgroup_id, data):
    r = get_session().put((get_base_url() + PUBLISHERS_URL) % adgroup_id, json=data)
    return _try_json(r)


def delete_publisher_group(account_id, publisher_group_id):
    r = get_session().delete((get_base_url() + PUBLISHER_GROUPS_URL + str(publisher_group_id)) % account_id)
    return _try_json(r)


# bulk upload


def bulk_upload_post(ad_groups):
    r = get_session().post(get_base_url() + BULK_UPLOAD_URL, json=ad_groups)
    return _try_json(r)


def bulk_upload_get(task_id):
    r = get_session().get(get_base_url() + BULK_UPLOAD_URL + task_id)
    return _try_json(r)


# books closed


def get_books_closed():
    r = get_session().get(get_base_url() + BOOKS_CLOSED_URL)
    return _try_json(r)
