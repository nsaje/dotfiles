import copy
import logging
import os
import random
import string
import StringIO
import unicodecsv

from django.conf import settings

from dash import models
from utils import s3helpers

logger = logging.getLogger(__name__)

OUTBRAIN_AGENCY = 55

EXAMPLE_CSV_CONTENT = [{
    "publisher": "example.com",
    "source": "mopub",
}, {
    "publisher": "examplenosource.com",
    "source": "",
}]


def get_csv_content(account, publisher_group_entries):
    output = StringIO.StringIO()
    writer = unicodecsv.writer(output, encoding='utf-8', dialect='excel', quoting=unicodecsv.QUOTE_ALL)

    is_outbrain = account.agency is not None and account.agency.id == OUTBRAIN_AGENCY
    add_outbrain_publisher_id = is_outbrain and any((entry.outbrain_publisher_id or
                                                     entry.outbrain_section_id or
                                                     entry.outbrain_amplify_publisher_id or
                                                     entry.outbrain_engage_publisher_id) for entry in publisher_group_entries)

    headers = ['Publisher', 'Source']
    if add_outbrain_publisher_id:
        headers.append('Outbrain Publisher Id')
        headers.append('Outbrain Section Id')
        headers.append('Outbrain Amplify Publisher Id')
        headers.append('Outbrain Engage Publisher Id')
    writer.writerow(headers)

    for entry in publisher_group_entries.order_by('publisher'):
        row = [entry.publisher, entry.source.get_clean_slug() if entry.source else None]
        if add_outbrain_publisher_id:
            row.append(entry.outbrain_publisher_id)
            row.append(entry.outbrain_section_id)
            row.append(entry.outbrain_amplify_publisher_id)
            row.append(entry.outbrain_engage_publisher_id)
        writer.writerow(row)

    return output.getvalue()


def get_example_csv_content():
    output = StringIO.StringIO()
    writer = unicodecsv.writer(output, encoding='utf-8', dialect='excel', quoting=unicodecsv.QUOTE_ALL)
    writer.writerow(('Publisher', 'Source'))
    for entry in EXAMPLE_CSV_CONTENT:
        writer.writerow((entry['publisher'], entry['source']))

    return output.getvalue()


def validate_entries(entry_dicts):
    validated_entry_dicts = []
    sources_by_slug = {x.get_clean_slug(): x for x in models.Source.objects.all()}

    for entry in entry_dicts:
        # these two will get modified for validation purposes
        publisher = entry['publisher']
        source_slug = entry['source']

        error = []

        prefixes = ('http://', 'https://')
        if any(publisher.startswith(x) for x in prefixes):
            error.append("Remove the following prefixes: http, https")

        # these were already validated, remove so they won't cause false errors in further validation
        for prefix in ('http://', 'https://'):
            publisher = publisher.replace(prefix, '')

        if '/' in publisher:
            error.append("'/' should not be used")

        validated_entry = copy.copy(entry)
        if 'error' in validated_entry:
            del validated_entry['error']

        if source_slug:
            if source_slug.lower() not in sources_by_slug:
                error.append("Unknown source")
        else:
            validated_entry['source'] = None

        if error:
            validated_entry['error'] = "; ".join(error)
        validated_entry_dicts.append(validated_entry)
    return validated_entry_dicts


def clean_entry_sources(entry_dicts):
    sources_by_slug = {x.get_clean_slug(): x for x in models.Source.objects.all()}
    for entry in entry_dicts:
        entry['source'] = sources_by_slug.get(entry['source'].lower())


def get_entries_errors_csv_content(account, entry_dicts):
    output = StringIO.StringIO()
    writer = unicodecsv.writer(output, encoding='utf-8', dialect='excel', quoting=unicodecsv.QUOTE_ALL)

    is_outbrain = account.agency is not None and account.agency.id == OUTBRAIN_AGENCY
    add_outbrain_publisher_id = is_outbrain and any(('outbrain_publisher_id' in entry_dict or
                                                     'outbrain_section_id' in entry_dict or
                                                     'outbrain_amplify_publisher_id' in entry_dict or
                                                     'outbrain_engage_publisher_id' in entry_dict) for entry_dict in entry_dicts)

    headers = ['Publisher', 'Source', 'Error']
    if add_outbrain_publisher_id:
        headers.insert(-1, 'Outbrain Publisher Id')
        headers.insert(-1, 'Outbrain Section Id')
        headers.insert(-1, 'Outbrain Amplify Publisher Id')
        headers.insert(-1, 'Outbrain Engage Publisher Id')

    writer.writerow(headers)
    for entry in entry_dicts:
        row = [
            entry['publisher'],
            entry['source'],
            entry.get('error')
        ]
        if add_outbrain_publisher_id:
            row.insert(-1, entry.get('outbrain_publisher_id'))
            row.insert(-1, entry.get('outbrain_section_id'))
            row.insert(-1, entry.get('outbrain_amplify_publisher_id'))
            row.insert(-1, entry.get('outbrain_engage_publisher_id'))
        writer.writerow(row)
    return output.getvalue()


def save_entries_errors_csv(account, entry_dicts):
    csv_content = get_entries_errors_csv_content(account, entry_dicts)
    csv_key = ''.join(random.choice(string.letters + string.digits) for _ in range(64))
    s3_helper = s3helpers.S3Helper(settings.S3_BUCKET_PUBLISHER_GROUPS)
    s3_helper.put(os.path.join(
        'publisher_group_errors', 'account_{}'.format(account.id), csv_key + '.csv'), csv_content)

    return csv_key
