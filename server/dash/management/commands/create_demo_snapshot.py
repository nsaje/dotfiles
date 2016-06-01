import datetime
import collections
import itertools
import os
import urllib
import urllib2
import sys

import faker


from django.db import models, connection, transaction
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.conf import settings
from django.core.serializers import serialize
from django.template import Variable, VariableDoesNotExist

import dash.models
import zemauth.models
from utils.command_helpers import ExceptionCommand
from utils import demo_anonymizer, s3helpers, request_signer

import logging
logger = logging.getLogger(__name__)

demo_anonymizer.set_fake_factory(faker.Faker())

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


@receiver(pre_save)
def pre_save_handler(sender, instance, *args, **kwargs):
    raise Exception("Do not save inside the demo data dump command!")


class Command(ExceptionCommand):
    help = """ Create a DB snapshot for demo deploys. """

    def handle(self, *args, **options):
        demo_mappings = dash.models.DemoMapping.objects.all()

        serialize_list = collections.OrderedDict()
        prepare_demo_objects(serialize_list, demo_mappings)
        dump_data = serialize('json', [obj for obj in reversed(serialize_list) if obj is not None], indent=4)

        snapshot_id = datetime.datetime.utcnow().strftime("%Y-%m-%d_%H%M")
        s3_helper = s3helpers.S3Helper(settings.S3_BUCKET_DEMO)
        s3_helper.put(os.path.join(snapshot_id, 'dump.json'), dump_data)
        s3_helper.put(os.path.join(snapshot_id, 'build.txt'), str(settings.BUILD_NUMBER))
        s3_helper.put('latest.txt', snapshot_id)

        # _deploykitty_prepare(snapshot_id)

        logger.info("QUERIES: %s", len(connection.queries))


def _deploykitty_prepare(snapshot_id):
    request = urllib2.Request(settings.DK_DEMO_PREPARE_ENDPOINT + '?' + urllib.urlencode({'version': snapshot_id}))
    request_signer.urllib2_secure_open(request, settings.DK_API_KEY)


@transaction.atomic()
def prepare_demo_objects(serialize_list, demo_mappings):
    demo_users = zemauth.models.User.objects.filter(email__endswith='test@test.com')
    demo_users_set = set(demo_users)

    anonymized_objects = set()
    for demo_mapping in demo_mappings:
        name_pools = demo_anonymizer.DemoNamePools(
            [demo_mapping.demo_account_name],
            demo_mapping.demo_campaign_name_pool,
            demo_mapping.demo_ad_group_name_pool)
        demo_anonymizer.set_name_pools(name_pools)

        account = dash.models.Account.objects.prefetch_related(
            *ACCOUNT_DUMP_SETTINGS['prefetch_related']
        ).get(pk=demo_mapping.real_account_id)

        # set demo users as the users of the future demo account
        account.users = demo_users

        # extract dependencies and anonymize
        start_extracting_at = len(serialize_list)
        _add_object_dependencies(serialize_list, account, ACCOUNT_DUMP_SETTINGS['dependents'])
        _extract_dependencies_and_anonymize(serialize_list, demo_users_set, anonymized_objects, start_extracting_at)

    # SAFETY CHECK: rollback at the end to prevent accidental changes to production DB
    transaction.set_rollback(True)


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


def _extract_dependencies_and_anonymize(serialize_list, demo_users_set, anonymized_objects, start_at=0):
    for obj in itertools.islice(serialize_list, start_at, None):
        anonymize = getattr(obj, '_demo_fields', {})
        if obj in demo_users_set or obj in anonymized_objects:  # don't anonymize demo users
            anonymize = {}

        for field in _get_fields(obj):
            if field.name in anonymize:
                setattr(obj, field.name, anonymize[field.name]())
                anonymized_objects.add(obj)
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
