import datetime
import boto
import boto.s3

from dateutil import rrule
from collections import defaultdict

from dash import constants

from utils import dates_helper


def get_local_date_query(date):
    context = get_local_date_context(date)

    query = """
    (date = '{date}' and hour is null) or (
        hour is not null and (
            (date = '{tzdate_from}' and hour >= {tzhour_from}) or
            (date = '{tzdate_to}' and hour < {tzhour_to})
        )
    )
    """.format(**context)
    return query


def get_local_date_context(date):
    """
    Prepare a date time context for aggregation of data by local time zone from UTC hourly data in the stats table.
    """

    hour_from = dates_helper.local_to_utc_time(datetime.datetime(date.year, date.month, date.day))
    date_next = date + datetime.timedelta(days=1)
    hour_to = dates_helper.local_to_utc_time(datetime.datetime(date_next.year, date_next.month, date_next.day))

    return {
        'date': date.isoformat(),
        'tzdate_from': hour_from.date().isoformat(),
        'tzhour_from': hour_from.hour,
        'tzdate_to': hour_to.date().isoformat(),
        'tzhour_to': hour_to.hour,
    }


def get_local_multiday_date_context(date_from, date_to):
    """
    Prepare a date time context for multiday aggregation of data by local time zone
    from UTC hourly data in the stats table.
    """

    from_context = get_local_date_context(date_from)
    to_context = get_local_date_context(date_to)

    date_ranges = []
    for date in rrule.rrule(rrule.DAILY, dtstart=date_from, until=date_to):
        date_ranges.append(get_local_date_context(date.date()))

    return {
        'date_from': from_context['date'],
        'date_to': to_context['date'],
        'tzdate_from': from_context['tzdate_from'],
        'tzhour_from': from_context['tzhour_from'],
        'tzdate_to': to_context['tzdate_to'],
        'tzhour_to': to_context['tzhour_to'],
        'date_ranges': date_ranges,
    }


def calculate_effective_cost(cost, data_cost, factors):
    pct_actual_spend, pct_license_fee = factors

    effective_cost = cost * pct_actual_spend
    effective_data_cost = data_cost * pct_actual_spend
    license_fee = (effective_cost + effective_data_cost) * pct_license_fee

    return effective_cost, effective_data_cost, license_fee


def extract_source_slug(source_slug):
    if not source_slug:
        return None

    if source_slug.startswith('b1_'):
        return source_slug[3:]
    return source_slug


def extract_device_type(device_type):
    if device_type == 1:
        return constants.DeviceType.MOBILE
    elif device_type == 2:
        return constants.DeviceType.DESKTOP
    elif device_type == 5:
        return constants.DeviceType.TABLET
    return constants.DeviceType.UNDEFINED


def extract_country(country):
    if country and len(country) == 2:
        return country.upper()
    return None


def extract_state(state):
    if state and len(state) <= 5:
        return state.upper()
    return None


def extract_dma(dma):
    if 499 < dma < 1000:
        return dma
    return None


def extract_age(age):
    if not age:
        return constants.AgeGroup.UNDEFINED

    age = age.strip()
    if age == '18-20':
        return constants.AgeGroup.AGE_18_20
    elif age == '21-29':
        return constants.AgeGroup.AGE_21_29
    elif age == '30-39':
        return constants.AgeGroup.AGE_30_39
    elif age == '40-49':
        return constants.AgeGroup.AGE_40_49
    elif age == '50-64':
        return constants.AgeGroup.AGE_50_64
    elif age == '65+':
        return constants.AgeGroup.AGE_65_MORE
    return constants.AgeGroup.UNDEFINED


def extract_gender(gender):
    if not gender:
        return constants.Gender.UNDEFINED

    gender = gender.strip()
    if gender == 'female':
        return constants.Gender.WOMEN
    elif gender == 'male':
        return constants.Gender.MEN
    return constants.Gender.UNDEFINED


def extract_age_gender(age, gender):
    mapping = {
        constants.Gender.WOMEN: {
            constants.AgeGroup.AGE_18_20: constants.AgeGenderGroup.AGE_18_20_WOMEN,
            constants.AgeGroup.AGE_21_29: constants.AgeGenderGroup.AGE_21_29_WOMEN,
            constants.AgeGroup.AGE_30_39: constants.AgeGenderGroup.AGE_30_39_WOMEN,
            constants.AgeGroup.AGE_40_49: constants.AgeGenderGroup.AGE_40_49_WOMEN,
            constants.AgeGroup.AGE_50_64: constants.AgeGenderGroup.AGE_50_64_WOMEN,
            constants.AgeGroup.AGE_65_MORE: constants.AgeGenderGroup.AGE_65_MORE_WOMEN,
        },
        constants.Gender.MEN: {
            constants.AgeGroup.AGE_18_20: constants.AgeGenderGroup.AGE_18_20_MEN,
            constants.AgeGroup.AGE_21_29: constants.AgeGenderGroup.AGE_21_29_MEN,
            constants.AgeGroup.AGE_30_39: constants.AgeGenderGroup.AGE_30_39_MEN,
            constants.AgeGroup.AGE_40_49: constants.AgeGenderGroup.AGE_40_49_MEN,
            constants.AgeGroup.AGE_50_64: constants.AgeGenderGroup.AGE_50_64_MEN,
            constants.AgeGroup.AGE_65_MORE: constants.AgeGenderGroup.AGE_65_MORE_MEN,
        },
        constants.Gender.UNDEFINED: {
            constants.AgeGroup.AGE_18_20: constants.AgeGenderGroup.AGE_18_20_UNDEFINED,
            constants.AgeGroup.AGE_21_29: constants.AgeGenderGroup.AGE_21_29_UNDEFINED,
            constants.AgeGroup.AGE_30_39: constants.AgeGenderGroup.AGE_30_39_UNDEFINED,
            constants.AgeGroup.AGE_40_49: constants.AgeGenderGroup.AGE_40_49_UNDEFINED,
            constants.AgeGroup.AGE_50_64: constants.AgeGenderGroup.AGE_50_64_UNDEFINED,
            constants.AgeGroup.AGE_65_MORE: constants.AgeGenderGroup.AGE_65_MORE_UNDEFINED,
        },
    }

    if gender in mapping:
        return mapping[gender].get(age, constants.AgeGenderGroup.UNDEFINED)

    return constants.AgeGenderGroup.UNDEFINED


def get_highest_priority_postclick_source(rows_by_postclick_source):
    return rows_by_postclick_source.get(
        'gaapi', rows_by_postclick_source.get(
            'ga_mail', rows_by_postclick_source.get(
                'omniture', rows_by_postclick_source.get(
                    'other', []))))


def extract_postclick_source(postclick_source):
    if postclick_source in ('gaapi', 'ga_mail', 'omniture'):
        return postclick_source
    return 'other'


def get_breakdown_key_for_postclickstats(source_id, content_ad_id):
    # this is a helper function just so that we don't mess up the order of these

    return (source_id, content_ad_id)


def get_aws_credentials_string(aws_access_key_id, aws_secret_access_key):
    return 'aws_access_key_id={key};aws_secret_access_key={secret}'.format(
        key=aws_access_key_id,
        secret=aws_secret_access_key,
    )


def get_aws_credentials_from_role():
    s3_client = boto.s3.connect_to_region('us-east-1')

    access_key = s3_client.aws_access_key_id
    access_secret = s3_client.aws_secret_access_key

    security_token_param = ''
    if s3_client.provider.security_token:
        security_token_param = ';token=%s' % s3_client.provider.security_token

    return 'aws_access_key_id=%s;aws_secret_access_key=%s%s' % (
        access_key, access_secret, security_token_param)
