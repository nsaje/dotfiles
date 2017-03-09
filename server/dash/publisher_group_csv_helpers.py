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


EXAMPLE_CSV_CONTENT = [{
    "publisher": "example.com",
    "source": "mopub",
}, {
    "publisher": "examplenosource.com",
    "source": "",
}]


def get_csv_content(publisher_group_entries):
    output = StringIO.StringIO()
    writer = unicodecsv.writer(output, encoding='utf-8', dialect='excel', quoting=unicodecsv.QUOTE_ALL)
    writer.writerow(('Publisher', 'Source'))
    for entry in publisher_group_entries.order_by('publisher'):
        writer.writerow((entry.publisher, entry.source))

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

        prefixes = ('http://', 'https://', 'www.')
        if any(publisher.startswith(x) for x in prefixes):
            error.append("Remove the following prefixes: http, https, www")

        # these were already validated, remove so they won't cause false errors in further validation
        for prefix in ('http://', 'https://', 'www.'):
            publisher = publisher.replace(prefix, '')

        if '/' in publisher:
            error.append("'/' should not be used")

        validated_entry = copy.copy(entry)

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


def save_entries_errors_csv(account_id, entry_dicts):
    output = StringIO.StringIO()
    writer = unicodecsv.writer(output, encoding='utf-8', dialect='excel', quoting=unicodecsv.QUOTE_ALL)
    writer.writerow(('Publisher', 'Source', 'Error'))
    for entry in entry_dicts:
        writer.writerow((
            entry['publisher'],
            entry['source'],
            entry.get('error'))
        )

    csv_key = ''.join(random.choice(string.letters + string.digits) for _ in range(64))
    s3_helper = s3helpers.S3Helper(settings.S3_BUCKET_PUBLISHER_GROUPS)
    s3_helper.put(os.path.join(
        'publisher_group_errors', 'account_{}'.format(account_id), csv_key + '.csv'), output.getvalue())

    return csv_key
