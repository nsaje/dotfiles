import datetime
import collections
import itertools
import json
import os
import urllib
import urllib2
import sys

import faker

from django.db import models, transaction
from django.db.models.signals import pre_save
from django.conf import settings
from django.core.serializers import serialize
from django.template import Variable, VariableDoesNotExist

from dash import constants
import dash.models
import zemauth.models
from utils.command_helpers import ExceptionCommand
from utils import demo_anonymizer, s3helpers, request_signer, json_helper

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
    # These are the attributes/methods of the model that we wish to dump.
    # We only need to list one-to-many and many-to-many fields, foreign key
    # dependencies are fetched automatically.
    'dependents': [
        'get_current_settings',
        'credits.all',
        'conversionpixel_set.all',
        {
            'primary': 'campaign_set.all',
            'dependents': [
                'get_current_settings',
                'budgets.all',
                {
                    'primary': 'campaigngoal_set.all',
                    'dependents': [
                        'values.all'
                    ]
                },
                {
                    'primary': 'adgroup_set.all',
                    'dependents': [
                        'get_current_settings',
                        {
                            'primary': 'adgroupsource_set.all',
                            'dependents': [
                                'get_current_settings'
                            ]
                        },
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


def pre_save_handler(sender, instance, *args, **kwargs):
    raise Exception("Do not save inside the demo data dump command!")


def _set_postgres_read_only(db_settings):
    db_options = db_settings.setdefault('OPTIONS', {})
    existing_pg_options = db_options.setdefault('options', '')
    db_options['options'] = ' '.join(['-c default_transaction_read_only=on', existing_pg_options])


class Command(ExceptionCommand):
    help = """ Create a DB snapshot for demo deploys. """

    def handle(self, *args, **options):
        # prevent explicit model saves
        pre_save.connect(pre_save_handler)
        # put connection in read-only mode
        _set_postgres_read_only(settings.DATABASES['default'])

        # perform inside transaction and rollback to be safe
        with transaction.atomic():
            demo_mappings = dash.models.DemoMapping.objects.all()
            demo_users_set = set(zemauth.models.User.objects.filter(email__endswith='+demo@zemanta.com'))

            serialize_list = collections.OrderedDict()
            prepare_demo_objects(serialize_list, demo_mappings, demo_users_set)
            dump_data = serialize('python', [obj for obj in reversed(serialize_list) if obj is not None])
            attach_demo_users(dump_data, demo_users_set)

            # roll back any changes we might have made (shouldn't be any)
            transaction.set_rollback(True)

        dump_json = json.dumps(dump_data, indent=4, cls=json_helper.JSONEncoder)
        snapshot_id = _get_snapshot_id()
        s3_helper = s3helpers.S3Helper(settings.S3_BUCKET_DEMO)
        s3_helper.put(os.path.join(snapshot_id, 'dump.json'), dump_json)
        s3_helper.put(os.path.join(snapshot_id, 'build.txt'), str(settings.BUILD_NUMBER))
        s3_helper.put('latest.txt', snapshot_id)

        _deploykitty_prepare(snapshot_id)


def _get_snapshot_id():
    return datetime.datetime.utcnow().strftime("%Y-%m-%d_%H%M")


def _deploykitty_prepare(snapshot_id):
    request = urllib2.Request(settings.DK_DEMO_PREPARE_ENDPOINT + '?' + urllib.urlencode({'version': snapshot_id}))
    request_signer.urllib2_secure_open(request, settings.DK_API_KEY)


def _create_fake_credit(account):
    return dash.models.CreditLineItem(
        id=1,
        account=account,
        amount=5000.0,
        start_date=datetime.date.today(),
        end_date=datetime.date.today() + datetime.timedelta(days=30),
        status=constants.CreditLineItemStatus.SIGNED,
        created_dt=datetime.datetime.utcnow(),
        modified_dt=datetime.datetime.utcnow(),
    )


def prepare_demo_objects(serialize_list, demo_mappings, demo_users_set):
    anonymized_objects = set()

    # add demo users
    _add_to_serialize_list(serialize_list, list(demo_users_set))
    _extract_dependencies_and_anonymize(serialize_list, demo_users_set, anonymized_objects)

    # add demo accounts
    for demo_mapping in demo_mappings:
        name_pools = demo_anonymizer.DemoNamePools(
            [demo_mapping.demo_account_name],
            demo_mapping.demo_campaign_name_pool,
            demo_mapping.demo_ad_group_name_pool)
        demo_anonymizer.set_name_pools(name_pools)

        account = dash.models.Account.objects.prefetch_related(
            *ACCOUNT_DUMP_SETTINGS['prefetch_related']
        ).get(pk=demo_mapping.real_account_id)

        # create fake credit so each account has at least some
        fake_credit = _create_fake_credit(account)

        # extract dependencies and anonymize
        start_extracting_at = len(serialize_list)
        _add_explicit_object_dependents(serialize_list, account, ACCOUNT_DUMP_SETTINGS['dependents'])
        _add_to_serialize_list(serialize_list, [fake_credit])
        _extract_dependencies_and_anonymize(serialize_list, demo_users_set, anonymized_objects, start_extracting_at)


def attach_demo_users(dump_data, demo_users_set):
    demo_users_pks = set(demo_user.pk for demo_user in demo_users_set)
    demo_account_pks = []
    demo_users_objs = []
    demo_account_objs = []
    for entity in dump_data:
        if entity['model'] == 'dash.account':
            demo_account_objs.append(entity)
            demo_account_pks.append(entity['pk'])
        if entity['pk'] in demo_users_pks:
            demo_users_objs.append(entity)
    for demo_user in demo_users_objs:
        demo_user['accounts'] = list(demo_account_pks)
    for demo_account in demo_account_objs:
        demo_account['users'] = list(demo_users_pks)


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


def _add_to_serialize_list(serialize_list, objs):
    for obj in objs:
        if obj is None:
            continue
        if not hasattr(obj, '_meta'):
            _add_to_serialize_list(serialize_list, obj)
            continue

        # ignore newly created objects (for example by get_current_settings)
        if obj.pk is None:
            continue

        # Proxy models don't serialize well in Django.
        if obj._meta.proxy:
            obj = obj._meta.proxy_for_model.objects.get(pk=obj.pk)

        # explanation: django ORM hashes model objects by PK so we need to save
        # the object as well, since it might hold anonymization changes
        if obj not in serialize_list:
            serialize_list[obj] = obj
        else:  # move to end
            obj = serialize_list[obj]
            del serialize_list[obj]
            serialize_list[obj] = obj


def _add_explicit_object_dependents(serialize_list, obj, dependencies):
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
                    _add_explicit_object_dependents(serialize_list, new_obj, sub_deps)
        except VariableDoesNotExist:
            sys.stderr.write('%s not found' % dep)

    if not dependencies:
        _add_to_serialize_list(serialize_list, [obj])


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
