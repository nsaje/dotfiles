from restapi.common.views_base_test import RESTAPITest
from django.core.urlresolvers import reverse

import restapi.serializers
import dash.models
from dash import constants
from utils.magic_mixer import magic_mixer


class CampaignsTest(RESTAPITest):

    @classmethod
    def campaign_repr(
        cls,
        id=123,
        account_id=321,
        archived=False,
        iab_category=constants.IABCategory.IAB1_1,
        language=constants.Language.ENGLISH,
        name='My Campaign TEST',
        enable_ga_tracking=True,
        ga_tracking_type=constants.GATrackingType.EMAIL,
        ga_property_id='',
        enable_adobe_tracking=False,
        adobe_tracking_param='cid',
        whitelist_publisher_groups=[153],
        blacklist_publisher_groups=[154],
        target_devices=[constants.AdTargetDevice.DESKTOP],
        target_placements=[constants.Placement.APP],
        target_os=[{'name': constants.OperatingSystem.ANDROID}, {'name': constants.OperatingSystem.LINUX}],
    ):
        representation = {
            'id': str(id),
            'accountId': str(account_id),
            'archived': archived,
            'iabCategory': constants.IABCategory.get_name(iab_category),
            'language': constants.Language.get_name(language),
            'name': name,
            'tracking': {
                'ga': {
                    'enabled': enable_ga_tracking,
                    'type': constants.GATrackingType.get_name(ga_tracking_type),
                    'webPropertyId': ga_property_id,
                },
                'adobe': {
                    'enabled': enable_adobe_tracking,
                    'trackingParameter': adobe_tracking_param,
                }
            },
            'targeting': {
                'devices': restapi.serializers.targeting.DevicesSerializer(target_devices).data,
                'placements': restapi.serializers.targeting.PlacementsSerializer(target_placements).data,
                'os': restapi.serializers.targeting.OSsSerializer(target_os).data,
                'publisherGroups': {
                    'included': whitelist_publisher_groups,
                    'excluded': blacklist_publisher_groups,
                }
            },
        }
        return cls.normalize(representation)

    def validate_against_db(self, campaign):
        campaign_db = dash.models.Campaign.objects.get(pk=campaign['id'])
        settings_db = campaign_db.settings
        expected = self.campaign_repr(
            id=campaign_db.id,
            account_id=campaign_db.account_id,
            archived=settings_db.archived,
            iab_category=settings_db.iab_category,
            language=settings_db.language,
            name=settings_db.name,
            enable_ga_tracking=settings_db.enable_ga_tracking,
            ga_tracking_type=settings_db.ga_tracking_type,
            ga_property_id=settings_db.ga_property_id,
            enable_adobe_tracking=settings_db.enable_adobe_tracking,
            adobe_tracking_param=settings_db.adobe_tracking_param,
            whitelist_publisher_groups=settings_db.whitelist_publisher_groups,
            blacklist_publisher_groups=settings_db.blacklist_publisher_groups,
            target_devices=settings_db.target_devices,
            target_placements=settings_db.target_placements,
            target_os=settings_db.target_os,
        )
        self.assertEqual(expected, campaign)

    def test_campaigns_get(self):
        r = self.client.get(reverse('campaigns_details', kwargs={'campaign_id': 308}))
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json['data'])

    def test_campaigns_put(self):
        test_campaign = self.campaign_repr(id=608, account_id=186, name="My test campaign!")
        r = self.client.put(
            reverse('campaigns_details', kwargs={'campaign_id': 608}),
            data=test_campaign,
            format='json'
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json['data'])
        self.assertEqual(resp_json['data'], test_campaign)

    def test_campaigns_put_empty(self):
        put_data = {}
        settings_count = dash.models.CampaignSettings.objects.filter(campaign_id=608).count()
        r = self.client.put(
            reverse('campaigns_details', kwargs={'campaign_id': 608}),
            data=put_data,
            format='json',
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json['data'])
        self.assertEqual(settings_count, dash.models.CampaignSettings.objects.filter(campaign_id=608).count())

    def test_campaigns_put_archive_restore(self):
        r = self.client.put(
            reverse('campaigns_details', kwargs={'campaign_id': 308}),
            data={'archived': True},
            format='json',
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json['data'])
        self.assertEqual(resp_json['data']['archived'], True)

        r = self.client.put(
            reverse('campaigns_details', kwargs={'campaign_id': 308}),
            data={'archived': False},
            format='json',
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json['data'])
        self.assertEqual(resp_json['data']['archived'], False)

    def test_campaigns_list(self):
        r = self.client.get(reverse('campaigns_list'))
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json['data']:
            self.validate_against_db(item)

    def test_campaigns_list_account_id(self):
        account_id = 186
        r = self.client.get(reverse('campaigns_list'), data={'accountId': account_id})
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json['data']:
            self.validate_against_db(item)
            self.assertEqual(int(item['accountId']), account_id)

    def test_campaigns_list_account_id_invalid(self):
        r = self.client.get(reverse('campaigns_list'), data={'accountId': 1000})
        self.assertResponseError(r, 'MissingDataError')

    def test_campaigns_list_pagination(self):
        account = magic_mixer.blend(dash.models.Account, users=[self.user])
        magic_mixer.cycle(10).blend(dash.models.Campaign, account=account)
        r = self.client.get(
            reverse('campaigns_list'),
            {'accountId': account.id},
        )
        r_paginated = self.client.get(
            reverse('campaigns_list'),
            {'accountId': account.id, 'limit': 2, 'offset': 5},
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        resp_json_paginated = self.assertResponseValid(r_paginated, data_type=list)
        self.assertEqual(resp_json['data'][5:7], resp_json_paginated['data'])

    def test_campaigns_post(self):
        new_campaign = self.campaign_repr(
            account_id=186,
            name='All About Testing',
            whitelist_publisher_groups=[153, 154],
            blacklist_publisher_groups=[]
        )
        del new_campaign['id']
        r = self.client.post(reverse('campaigns_list'), data=new_campaign, format='json')
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(resp_json['data'])
        new_campaign['id'] = resp_json['data']['id']
        self.assertEqual(resp_json['data'], new_campaign)

    def test_campaigns_post_no_account_id(self):
        new_campaign = self.campaign_repr(
            name='Its me, Account',
            whitelist_publisher_groups=[153, 154],
            blacklist_publisher_groups=[]
        )
        del new_campaign['id']
        del new_campaign['accountId']
        r = self.client.post(reverse('campaigns_list'), data=new_campaign, format='json')
        self.assertResponseError(r, 'ValidationError')

    def test_campaigns_post_wrong_account_id(self):
        new_campaign = self.campaign_repr(
            account_id=1000,
            name='Over 9000',
            whitelist_publisher_groups=[153, 154],
            blacklist_publisher_groups=[]
        )
        del new_campaign['id']
        r = self.client.post(reverse('campaigns_list'), data=new_campaign, format='json')
        self.assertResponseError(r, 'MissingDataError')

    def test_iab_tier_1(self):
        test_campaign = self.campaign_repr(
            id=608, account_id=186,
            name="My test campaign!",
            iab_category=constants.IABCategory.IAB21,
        )
        r = self.client.put(
            reverse('campaigns_details', kwargs={'campaign_id': 608}),
            data=test_campaign,
            format='json'
        )
        self.assertResponseError(r, 'ValidationError')

    def test_ga_property_id_validation(self):
        test_campaign = self.campaign_repr(
            id=608,
            account_id=186,
            name="My test campaign!",
            ga_property_id='PID',
        )
        r = self.client.put(
            reverse('campaigns_details', kwargs={'campaign_id': 608}),
            data=test_campaign,
            format='json'
        )
        self.assertResponseError(r, 'ValidationError')

    def test_language_validation(self):
        test_campaign = self.campaign_repr(
            id=608,
            account_id=186,
            name="My test campaign!",
            language=constants.Language.ARABIC,
        )
        r = self.client.put(
            reverse('campaigns_details', kwargs={'campaign_id': 608}),
            data=test_campaign,
            format='json'
        )
        self.assertResponseError(r, 'ValidationError')

    def test_adobe_tracking_parameter_blank(self):
        test_campaign = self.campaign_repr(
            id=608,
            account_id=186,
            name="Adobe tracking campaign",
            adobe_tracking_param='',
        )
        r = self.client.put(
            reverse('campaigns_details', kwargs={'campaign_id': 608}),
            data=test_campaign,
            format='json'
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json['data'])
