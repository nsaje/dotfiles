import datetime
import collections
import os
import urllib, urllib2
import sys

import faker
try:
    from django.db.models import loading
except ImportError:
    from django.apps import apps as loading
from django.db import models, connection
from django.conf import settings
from django.core.serializers import serialize
from django.template import Variable, VariableDoesNotExist

from utils.command_helpers import ExceptionCommand
from utils import demo_anonymizer, s3helpers, request_signer

import logging
logger = logging.getLogger(__name__)


ACCOUNT_DUMP_SETTINGS = {
    'primary': 'dash.account',  # This is our reference model.
    'prefetch_related': [  # Prefetch fields.
        'campaign_set__adgroup_set__contentad_set__contentadsource_set__source',
        'campaign_set__adgroup_set__adgroupsource_set__source__source_type',
        'campaign_set__adgroup_set__adgroupsource_set__source_credentials',
    ],
    'dependents': [  # These are the attributes/methods of the model that we wish to dump.
        'get_current_settings',
        {
            'primary': 'campaign_set.all',
            'dependents': [
                'get_current_settings',
                {
                    'primary': 'adgroup_set.all',
                    'dependents': [
                        'get_current_settings',
                        'adgroupsource_set.all',
                        {
                            'primary': 'contentad_set.all',
                            'dependents': [
                                'contentadsource_set.all'
                            ]
                        }
                    ]
                }
            ]
        }
    ],
}


class Command(ExceptionCommand):
    help = """ Create a DB snapshot for demo deploys. """

    def handle(self, *args, **options):
        real_account_pks = [279]  # TODO: get this from DB
        demo_anonymizer.set_fake_factory(faker.Faker())

        serialize_list = collections.OrderedDict()
        _prepare_objects(serialize_list, real_account_pks)
        dump_data = serialize('json', [obj for obj in reversed(serialize_list) if obj is not None], indent=4)

        snapshot_id = datetime.datetime.utcnow().strftime("%Y-%m-%d_%H%M")
        s3_helper = s3helpers.S3Helper(settings.S3_BUCKET_DEMO)
        s3_helper.put(os.path.join(snapshot_id, 'dump.json'), dump_data)
        s3_helper.put(os.path.join(snapshot_id, 'build.txt'), str(settings.BUILD_NUMBER))
        s3_helper.put('latest.txt', snapshot_id)

        _deploykitty_prepare(snapshot_id)

        logger.info("QUERIES: %s", len(connection.queries))


def _deploykitty_prepare(snapshot_id):
    request = urllib2.Request(settings.DK_DEMO_PREPARE_ENDPOINT + '?' + urllib.urlencode({'version': snapshot_id}))
    request_signer.urllib2_secure_open(request, settings.DK_API_KEY)


def _prepare_objects(serialize_list, real_account_pks):
    demo_users = (loading.get_model('zemauth', 'User').objects.filter(email__endswith='test@test.com'))
    demo_users_set = set(demo_users)

    (app_label, model_name) = ACCOUNT_DUMP_SETTINGS['primary'].split('.')
    model_to_dump = loading.get_model(app_label, model_name)
    for real_account_pk in real_account_pks:
        # TODO: get this from DB
        name_pools = demo_anonymizer.DemoNamePools(
            ['Top 4 Mobile Carrier'],
            ['Brand Awareness Campaign', 'Earned Media Promotion & Retargeting', 'The Quiz'],
            ['Audio & Connected audience segment', 'Connected Family audience segment',
             'Full Feature audience segment', '4G LTE', 'Best Value for International Travel',
             'Waive early termination fee', 'Digital Moms', 'Hipsters', 'Teenagers'])
        demo_anonymizer.set_name_pools(name_pools)

        account = model_to_dump.objects.prefetch_related(
            *ACCOUNT_DUMP_SETTINGS['prefetch_related']
        ).get(pk=real_account_pk)

        # set demo users as the users of the future demo account
        account.users = demo_users

        # extract dependencies and anonymize
        _add_object_dependencies(serialize_list, account, ACCOUNT_DUMP_SETTINGS['dependents'])
        _extract_dependencies_and_anonymize(serialize_list, demo_users_set)  # FIXME: continue on from end


def _get_fields(obj):
    try:
        return obj._meta.fields
    except AttributeError:
        return []


def _get_many_to_many_fields(obj):
    try:
        return obj._meta.many_to_many
    except AttributeError:
        return []


def _extract_dependencies_and_anonymize(serialize_list, demo_users_set):
    for obj in serialize_list:
        anonymize = getattr(obj, '_demo_fields', {})
        if obj in demo_users_set:  # don't anonymize demo users
            anonymize = {}

        for field in _get_fields(obj):
            if field.name in anonymize:
                setattr(obj, field.name, anonymize[field.name]())
            if isinstance(field, models.ForeignKey):
                _add_to_serialize_list(serialize_list, [obj.__getattribute__(field.name)])
        for field in _get_many_to_many_fields(obj):
            _add_to_serialize_list(serialize_list, obj.__getattribute__(field.name).all())


def _add_to_serialize_list(serialize_list, objs):
    for obj in objs:
        if obj is None:
            continue
        if not hasattr(obj, '_meta'):
            _add_to_serialize_list(serialize_list, obj)
            continue

        # Proxy models don't serialize well in Django.
        if obj._meta.proxy:
            obj = obj._meta.proxy_for_model.objects.get(pk=obj.pk)

        if obj not in serialize_list:
            serialize_list[obj] = None
        else:  # move to end
            del serialize_list[obj]
            serialize_list[obj] = None


def _add_object_dependencies(serialize_list, obj, dependencies):
    # get the dependent objects and add to serialize list
    for dep in dependencies:
        try:
            if isinstance(dep, dict):
                sub_deps = dep['dependents']
                dep = dep['primary']
            else:
                sub_deps = None

            thing = Variable("thing.%s" % dep).resolve({'thing': obj})
            _add_to_serialize_list(serialize_list, [thing])
            if sub_deps:
                for new_obj in thing:
                    _add_object_dependencies(serialize_list, new_obj, sub_deps)
        except VariableDoesNotExist:
            sys.stderr.write('%s not found' % dep)

    if not dependencies:
        _add_to_serialize_list(serialize_list, [obj])
