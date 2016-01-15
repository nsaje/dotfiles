import collections
from optparse import make_option

from django.core.management import BaseCommand
from django.core import serializers
from django.conf import settings
from django.db.models import Q

import dash.models
import zemauth.models
from utils.command_helpers import ExceptionCommand

HANDLE_MODIFYBY = (
    'dash_demo_adgroup',
    'dash_demo_campaign',
    'dash_demo_account',
)

DEMO_ID_OFFSET = 1000000

class Command(ExceptionCommand):
    option_list = BaseCommand.option_list + (
	make_option('--format', dest='format', default='json', help='Output format'),
    )
    def handle(self, *args, **options):
        app_list = collections.OrderedDict()

        demo_user = zemauth.models.User.objects.get(email=settings.DEMO_USER_EMAIL)

        real2demo = {}
        for d2r in dash.models.DemoAdGroupRealAdGroup.objects.all():
            real2demo[d2r.real_ad_group_id] = d2r.demo_ad_group_id

        app_list['zemauth_user'] = zemauth.models.User.objects.filter(
            Q(email__in=settings.DEMO_USERS) | Q(email='protractor@zemanta.com')
        )

        # Exclude sources with issues in demo data
        app_list['dash_source'] = dash.models.Source.objects.filter(
            deprecated=False
        ).filter(~Q(name='Connatix')).filter(~Q(name='Revenue.com'))
        app_list['dash_sourcetypes'] = dash.models.SourceType.objects.all()
        app_list['dash_sourcecredentials'] = dash.models.SourceCredentials.objects.all()
        for cred in app_list['dash_sourcecredentials']:
            cred.credentials = ''

        app_list['dash_demo_adgroup'] = dash.models.AdGroup.demo_objects.all()
        app_list['dash_demo_campaign'] = dash.models.Campaign.demo_objects.all()
        app_list['dash_demo_account'] = dash.models.Account.demo_objects.all()
        app_list['dash_demo_contentad'] = dash.models.ContentAd.objects.filter(
            ad_group__in=app_list['dash_demo_adgroup']
        )
        uploadbatch_ids = set(obj.batch_id for obj in app_list['dash_demo_contentad'])
        app_list['dash_demo_uploadbatch'] = dash.models.UploadBatch.objects.filter(
            id__in=uploadbatch_ids
        )
        app_list['dash_defaultsourcesettings'] = dash.models.DefaultSourceSettings.objects.filter(
            source__in=app_list['dash_source'],
        )

        app_list['dash_adgroupsource'] = dash.models.AdGroupSource.objects.filter(
            ad_group_id__in=real2demo.keys(),
            source__in=app_list['dash_source'],
        )

        for obj in app_list['dash_adgroupsource']:
            obj.ad_group_id = real2demo[obj.ad_group_id]

        app_list['dash_sourcecredentials'] = dash.models.SourceCredentials.objects.filter(
            source__in=app_list['dash_source'],
        )
        for obj in app_list['dash_sourcecredentials']:
            obj.credentials = ''

        for obj in app_list['dash_demo_account']:
            obj.users = app_list['zemauth_user']

        for model_name in HANDLE_MODIFYBY:
            for obj in app_list[model_name]:
                obj.modified_by = demo_user

        data = serializers.serialize(options['format'], serializers.sort_dependencies(
            app_list.items(),
        ), use_natural_foreign_keys=True)
        self.stdout.write(data)
