import datetime
import functools
import io
import json
import logging
import os
import signal
import sys
import tarfile

import faker
import influx
from django.conf import settings
from django.core.serializers import serialize
from django.db import connections
from django.db import models
from django.db import transaction
from django.db.models.signals import pre_save
from django.template import Variable
from django.template import VariableDoesNotExist

import dash.models
import demo
import demo.models
import zemauth.models
from dash import constants
from utils import demo_anonymizer
from utils import grouper
from utils import json_helper
from utils import s3helpers
from utils import unique_ordered_list
from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)

demo_anonymizer.set_fake_factory(faker.Faker())

TIMEOUT = 30 * 60

# due to cyclical foreign key dependency, we want to ignore some fields
IGNORE_FIELDS = {
    dash.models.PublisherGroup: {"account", "agency"},
    dash.models.AgencySettings: {"agency"},
    dash.models.AccountSettings: {"account"},
    dash.models.CampaignSettings: {"campaign"},
    dash.models.AdGroupSettings: {"ad_group"},
    dash.models.AdGroupSourceSettings: {"ad_group_source"},
}

ACCOUNT_DUMP_SETTINGS = {
    "primary": "dash.account",  # This is our reference model.
    "prefetch_related": [  # Prefetch fields.
        "campaign_set__adgroup_set__contentad_set__contentadsource_set__source",
        "campaign_set__adgroup_set__adgroupsource_set__source__source_type",
        "campaign_set__adgroup_set__adgroupsource_set__source_credentials",
    ],
    # These are the attributes/methods of the model that we wish to dump.
    # We only need to list one-to-many and many-to-many fields, foreign key
    # dependencies are fetched automatically.
    "dependents": [
        "credits.all",
        "conversionpixel_set.all",
        {
            "primary": "campaign_set.all",
            "dependents": [
                {"primary": "budgets.all", "dependents": ["statements.all"]},
                {"primary": "campaigngoal_set.all", "dependents": ["values.all"]},
                {
                    "primary": "adgroup_set.all",
                    "dependents": [
                        {"primary": "adgroupsource_set.all", "dependents": []},
                        {"primary": "contentad_set.all", "dependents": ["contentadsource_set.all"]},
                    ],
                },
            ],
        },
    ],
}

MAX_PER_FILE = 1000


def alarm_handler(*args, **kwargs):
    raise Exception("Create demo snapshot timed out!")


def _postgres_read_only(using="default"):
    def decorator(func):
        @functools.wraps(func)
        def f(*args, **kwargs):
            db_settings = settings.DATABASES[using]
            db_options = db_settings.setdefault("OPTIONS", {})
            old_pg_options = db_options.setdefault("options", "")
            readonly_option = "-c default_transaction_read_only=on"
            db_options["options"] = " ".join([readonly_option, old_pg_options])
            connections[using].connect()
            try:
                ret = func(*args, **kwargs)
            finally:
                db_options["options"] = old_pg_options
                connections[using].connect()
            return ret

        return f

    return decorator


class Command(ExceptionCommand):
    help = """ Create a DB snapshot for demo deploys. """

    # put connection in read-only mode
    @_postgres_read_only(using="default")
    def handle(self, *args, **options):
        if options.get("verbosity", 0) > 1:
            logger.setLevel(logging.DEBUG)
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            logger.addHandler(ch)

        signal.signal(signal.SIGALRM, alarm_handler)
        signal.alarm(TIMEOUT)

        # prevent explicit model saves
        pre_save.connect(_pre_save_handler)
        try:
            # perform inside transaction and rollback to be safe
            with transaction.atomic():
                demo_mappings = demo.models.DemoMapping.objects.all()
                demo_users_set = set(zemauth.models.User.objects.filter(email__endswith="+demo@zemanta.com"))
                demo_users_pks = set(demo_user.pk for demo_user in demo_users_set)

                serialize_list = unique_ordered_list.UniqueOrderedList()
                _prepare_demo_objects(serialize_list, demo_mappings, demo_users_set)

                # roll back any changes we might have made (shouldn't be any)
                transaction.set_rollback(True)

            snapshot_id = _get_snapshot_id()

            tarbuffer = io.BytesIO()
            tararchive = tarfile.open(mode="w", fileobj=tarbuffer)

            filtered_reversed_list = [obj for obj in reversed(list(serialize_list)) if obj is not None]
            grouped_list = grouper(MAX_PER_FILE, filtered_reversed_list)

            for i, group_data in enumerate(grouped_list):
                dump_group_data = serialize("python", group_data)
                _attach_demo_users(dump_group_data, demo_users_pks)
                _remove_entity_tags(dump_group_data)

                group_json = json.dumps(dump_group_data, indent=4, cls=json_helper.JSONEncoder)

                dumpbuffer = io.BytesIO()
                dumpbuffer.write(group_json.encode("utf-8"))

                info = tarfile.TarInfo("dump{i}.json".format(i=i))
                info.size = dumpbuffer.tell()

                dumpbuffer.seek(0)

                tararchive.addfile(info, fileobj=dumpbuffer)

            tararchive.close()

            build = str(settings.BUILD_NUMBER)
            if settings.BRANCH:
                build = settings.BRANCH + "/" + str(settings.BUILD_NUMBER)

            s3_helper = s3helpers.S3Helper(settings.S3_BUCKET_DEMO)
            s3_helper.put(os.path.join(snapshot_id, "dump.tar"), tarbuffer.getvalue())
            s3_helper.put(os.path.join(snapshot_id, "build.txt"), build)

            s3_helper.put("latest.txt", snapshot_id)
            influx.incr("create_demo_dump_to_s3", 1, status="success")

            demo.prepare_demo(snapshot_id)
        finally:
            pre_save.disconnect(_pre_save_handler)


def _pre_save_handler(sender, instance, *args, **kwargs):
    raise Exception("Do not save inside the demo data dump command!")


def _get_snapshot_id():
    return datetime.datetime.utcnow().strftime("%Y-%m-%d_%H%M")


def _prepare_demo_objects(serialize_list, demo_mappings, demo_users_set):
    anonymized_objects = set()

    # add demo users
    _add_to_serialize_list(serialize_list, list(demo_users_set))
    _extract_dependencies_and_anonymize(serialize_list, demo_users_set, anonymized_objects)

    # add sources
    default_source_settings = dash.models.DefaultSourceSettings.objects.all()
    _add_to_serialize_list(serialize_list, list(default_source_settings))
    _extract_dependencies_and_anonymize(serialize_list, demo_users_set, anonymized_objects)

    # add currencies
    currencies = dash.models.CurrencyExchangeRate.objects.all()
    _add_to_serialize_list(serialize_list, list(currencies))
    _extract_dependencies_and_anonymize(serialize_list, demo_users_set, anonymized_objects)

    # add BlueKai categories
    bluekai_categories = dash.models.BlueKaiCategory.objects.all()
    _add_to_serialize_list(serialize_list, list(bluekai_categories))
    _extract_dependencies_and_anonymize(serialize_list, demo_users_set, anonymized_objects)

    # add email templates
    email_templates = dash.models.EmailTemplate.objects.all()
    _add_to_serialize_list(serialize_list, list(email_templates))
    _extract_dependencies_and_anonymize(serialize_list, demo_users_set, anonymized_objects)

    # add demo accounts
    for demo_mapping in demo_mappings:
        name_pools = demo_anonymizer.DemoNamePools(
            [demo_mapping.demo_account_name], demo_mapping.demo_campaign_name_pool, demo_mapping.demo_ad_group_name_pool
        )
        demo_anonymizer.set_name_pools(name_pools)

        account = dash.models.Account.objects.prefetch_related(*ACCOUNT_DUMP_SETTINGS["prefetch_related"]).get(
            pk=demo_mapping.real_account_id
        )

        # create fake credit so each account has at least some
        fake_credit = _create_fake_credit(account)

        # create fake global blacklist
        fake_global_blacklist = _create_global_blacklist()

        # extract dependencies and anonymize
        _add_explicit_object_dependents(serialize_list, account, ACCOUNT_DUMP_SETTINGS["dependents"])
        _add_to_serialize_list(serialize_list, [fake_credit, fake_global_blacklist])
        _extract_dependencies_and_anonymize(serialize_list, demo_users_set, anonymized_objects)
        # TODO optimize somehow so we don't need to rescan the whole list for every account.
        # The reason we run _extract_dependencies_and_anonymize for every account is that
        # anonymizer name pools are globally scoped. Maybe we could figure out a way to anonymize
        # the correct objects with the correct name pools, or find a way to mark already extracted
        # items...
        # Comment by domen: Just an idea: could you do whatever you do in
        # _extract_dependencies_and_anonymize when you are adding objects in _add_to_serialize_list?
        # This way you would not have to loop over the serialize_list again.


def _create_fake_credit(account):
    return dash.models.CreditLineItem(
        id=1,
        account=account,
        amount=50000.0,
        start_date=datetime.date.today(),
        end_date=datetime.date.today() + datetime.timedelta(days=30),
        status=constants.CreditLineItemStatus.SIGNED,
        created_dt=datetime.datetime.utcnow(),
        modified_dt=datetime.datetime.utcnow(),
    )


def _create_global_blacklist():
    return dash.models.PublisherGroup(
        id=settings.GLOBAL_BLACKLIST_ID,
        name="Global blacklist",
        created_dt=datetime.datetime.now(),
        modified_dt=datetime.datetime.now(),
    )


def _attach_demo_users(dump_data, demo_users_pks):
    for entity in dump_data:
        if entity["model"] == "dash.account":
            entity["fields"]["users"] = list(demo_users_pks)


def _remove_entity_tags(dump_data):
    for entity in dump_data:
        entity["fields"].pop("entity_tags", None)


def _add_to_serialize_list(serialize_list, objs):
    for obj in objs:
        if obj is None:
            continue
        if not hasattr(obj, "_meta"):
            _add_to_serialize_list(serialize_list, obj)
            continue

        # ignore newly created objects (for example by get_current_settings)
        if obj.pk is None:
            continue

        # Proxy models don't serialize well in Django.
        if obj._meta.proxy:
            obj = obj._meta.proxy_for_model.objects.get(pk=obj.pk)

        serialize_list.add_or_move_to_end(obj)


def _add_explicit_object_dependents(serialize_list, obj, dependencies):
    # get the dependent objects and add to serialize list
    for dep in dependencies:
        try:
            if isinstance(dep, dict):
                sub_deps = dep["dependents"]
                dep = dep["primary"]
            else:
                sub_deps = None

            thing = Variable("thing.%s" % dep).resolve({"thing": obj})
            _add_to_serialize_list(serialize_list, [thing])
            if sub_deps:
                for new_obj in thing:
                    _add_explicit_object_dependents(serialize_list, new_obj, sub_deps)
        except VariableDoesNotExist:
            sys.stderr.write("%s not found" % dep)

    if not dependencies:
        _add_to_serialize_list(serialize_list, [obj])


def _extract_dependencies_and_anonymize(serialize_list, demo_users_set, anonymized_objects, start_at=0):
    for obj in serialize_list:
        logger.debug("%s %s" % (obj.__class__, obj))
        anonymize = getattr(obj, "_demo_fields", {})
        if obj in demo_users_set or obj in anonymized_objects:  # don't anonymize demo users
            anonymize = {}

        ignore_fields = IGNORE_FIELDS.get(obj.__class__, set())
        for field in _get_fields(obj):
            if field.name in anonymize:
                setattr(obj, field.name, anonymize[field.name]())
                anonymized_objects.add(obj)
            if (field.name not in ignore_fields) and isinstance(field, models.ForeignKey):
                logger.debug("adding child %s of %s" % (field.name, obj))
                _add_to_serialize_list(serialize_list, [obj.__getattribute__(field.name)])
        for field in _get_many_to_many_fields(obj):
            logger.debug("adding all children of %s" % obj)
            _add_to_serialize_list(serialize_list, obj.__getattribute__(field.name).all())


def _get_fields(obj):
    try:
        fields = list(obj._meta.fields)
        return fields
    except AttributeError:
        return []


def _get_many_to_many_fields(obj):
    try:
        return obj._meta.many_to_many
    except AttributeError:
        return []
