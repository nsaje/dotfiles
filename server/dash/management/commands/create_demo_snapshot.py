import collections
from django.db import models, connection
import faker

from utils.command_helpers import ExceptionCommand
from utils import demo_anonymizer

import sys

try:
    from django.db.models import loading
except ImportError:
    from django.apps import apps as loading
from django.core.serializers import serialize
from django.conf import settings
from django.template import Variable, VariableDoesNotExist


import logging
logger = logging.getLogger(__name__)


ACCOUNT_DUMP_SETTINGS = {
    'primary': 'dash.account',  # This is our reference model.
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

    def __init__(self):
        super(ExceptionCommand, self).__init__()
        self.serialize_list = collections.OrderedDict()
        self.name_pools = demo_anonymizer.DemoNamePools(
            ['Top 4 Mobile Carrier'],
            ['Brand Awareness Campaign', 'Earned Media Promotion & Retargeting', 'The Quiz'],
            ['Audio & Connected audience segment', 'Connected Family audience segment',
             'Full Feature audience segment', '4G LTE', 'Best Value for International Travel',
             'Waive early termination fee', 'Digital Moms', 'Hipsters', 'Teenagers'])
        self.demo_users_set = None

        demo_anonymizer.set_name_pools(self.name_pools)
        demo_anonymizer.set_fake_factory(faker.Faker())

    def handle(self, *args, **options):
        demo_users = loading.get_model('zemauth', 'User').objects.filter(email__endswith='test@test.com').prefetch_related(
            'groups__permissions__content_type',
            'user_permissions__content_type',
        )
        self.demo_users_set = set(demo_users)

        # pks = [168]
        pks = [279]
        # pks = [203]
        (app_label, model_name) = ACCOUNT_DUMP_SETTINGS['primary'].split('.')
        model_to_dump = loading.get_model(app_label, model_name)
        real_accounts = model_to_dump.objects.filter(pk__in=[int(i) for i in pks]).prefetch_related(
            'campaign_set__adgroup_set__contentad_set__contentadsource_set__source',
            'campaign_set__adgroup_set__adgroupsource_set__source__source_type',
            'campaign_set__adgroup_set__adgroupsource_set__source_credentials',
        )
        for account in real_accounts:
            account.users = demo_users
            self._add_object_dependencies(account, ACCOUNT_DUMP_SETTINGS['dependents'])
        self._serialize_fully()
        data = serialize('json', [o for o in self.serialize_list if o is not None],
                         indent=4)
        #  use_natural_foreign_keys=True, use_natural_primary_keys=True,

        self.stdout.write(data)
        # logger.info("QUERIES: %s", str(connection.queries))
        logger.info("QUERIES: %s", len(connection.queries))

    @staticmethod
    def _get_fields(obj):
        try:
            return obj._meta.fields
        except AttributeError:
            return []

    @staticmethod
    def _get_many_to_many_fields(obj):
        try:
            return obj._meta.many_to_many
        except AttributeError:
            return []

    def _serialize_fully(self):
        for obj in self.serialize_list:
            anonymize = getattr(obj, '_demo_fields', {})
            if obj in self.demo_users_set:  # don't anonymize demo users
                anonymize = {}
            for field in self._get_fields(obj):
                logger.info(str(obj) + ': ' + str(field))
                if field.name in anonymize:
                    logger.info("ANONYMIZING %s", field.name)
                    setattr(obj, field.name, anonymize[field.name]())
                if isinstance(field, models.ForeignKey):
                    self._add_to_serialize_list(
                        [obj.__getattribute__(field.name)])
            for field in self._get_many_to_many_fields(obj):
                logger.info(str(obj) + '; ' + str(field))
                self._add_to_serialize_list(
                    obj.__getattribute__(field.name).all())
        self.serialize_list = reversed(self.serialize_list)

    def _add_to_serialize_list(self, objs):
        for obj in objs:
            logger.info("self._add_to_serialize_list: obj: " + str(obj))
            if obj is None:
                continue
            if not hasattr(obj, '_meta'):
                self._add_to_serialize_list(obj)
                continue

            # Proxy models don't serialize well in Django.
            if obj._meta.proxy:
                obj = obj._meta.proxy_for_model.objects.get(pk=obj.pk)

            if obj not in self.serialize_list:
                self.serialize_list[obj] = None
            else:  # move to end
                logger.info("MOVING TO END: " + str(obj))
                del self.serialize_list[obj]
                self.serialize_list[obj] = None

    def _add_object_dependencies(self, obj, dependencies):
        # get the dependent objects and add to serialize list
        for dep in dependencies:
            try:
                if isinstance(dep, dict):
                    sub_deps = dep['dependents']
                    dep = dep['primary']
                else:
                    sub_deps = None

                thing = Variable("thing.%s" % dep).resolve({'thing': obj})
                self._add_to_serialize_list([thing])
                if sub_deps:
                    for new_obj in thing:
                        self._add_object_dependencies(new_obj, sub_deps)
            except VariableDoesNotExist:
                sys.stderr.write('%s not found' % dep)

        if not dependencies:
            self._add_to_serialize_list([obj])
