import argparse
import collections
from django.db import models, connection
import django

from utils.command_helpers import ExceptionCommand

import sys
try:
    import json
except ImportError:
    from django.utils import simplejson as json

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
        self.seen = {}

    def handle(self, *args, **options):
        settings.DEBUG = True

        demo_users = loading.get_model('zemauth', 'User').objects.filter(email__endswith='test@test.com').prefetch_related(
            'groups__permissions__content_type',
            'user_permissions__content_type',
        )

        # pks = [168]
        pks = [279]
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
                         use_natural_foreign_keys=True, use_natural_primary_keys=True,
                         indent=4)

        self.stdout.write(data)
        logger.info("QUERIES: %s", str(connection.queries))
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
            for field in self._get_fields(obj):
                logger.info(str(obj) + ': ' + str(field))
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
            # model_name = getattr(obj._meta, 'model_name',
            #                      getattr(obj._meta, 'module_name', None))
            # key = "%s:%s:%s" % (obj._meta.app_label, model_name, obj.pk)

            self.serialize_list[obj] = None
            # if key not in self.seen:
            #     self.serialize_list[obj] = None
            #     self.seen[key] = 1
            # else:  # move to end
            #     logger.info("MOVING TO END: " + str(obj))
            #     # idx = self.serialize_list.index(obj)
            #     # self.serialize_list[idx] = None
            #     # self.serialize_list.append(obj)
            #     del self.serialize_list[obj]
            #     self.serialize_list[obj] = None

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
