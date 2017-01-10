from mock import patch
import datetime

from django.test import TestCase
from django.http.request import HttpRequest

import dash.models
import dash.constants
import dash.blacklist
import zemauth.models

BLACKLISTED = dash.constants.PublisherStatus.BLACKLISTED
ENABLED = dash.constants.PublisherStatus.ENABLED


class BlacklistTestCase(TestCase):
    fixtures = ['test_api.yaml']

    def setUp(self):
        self.request = HttpRequest()
        self.request.user = zemauth.models.User.objects.get(id=1)

        self.ad_group = dash.models.AdGroup.objects.get(pk=1)
        self.campaign = self.ad_group.campaign
        self.account = self.campaign.account

        self.account.name = 'ZemAccount'
        self.account.save(self.request)

        self.source = dash.models.Source.objects.get(pk=1)
        self.domains = [
            ('www.google.com', None),
            ('www.zemanta.com', '123'),
            ('www.zemanata.com', 'abc'),
        ]
        self.domain_names = [d[0] for d in self.domains]
        self.ob = dash.models.Source.objects.get(
            source_type__type=dash.constants.SourceType.OUTBRAIN
        )
        self.ob.source_type.available_actions = [
            dash.constants.SourceAction.CAN_MODIFY_PUBLISHER_BLACKLIST_AUTOMATIC
        ]
        self.ob.source_type.save()

        # One always globally blacklisted:
        dash.models.PublisherBlacklist.objects.create(
            everywhere=True,
            name='www.donaldjtrump.com'
        )

    def test_global_blacklist_wrong_constraings(self):
        with self.assertRaises(Exception):
            dash.blacklist.update(self.ad_group, {'ad_group': self.ad_group},
                                  BLACKLISTED, everywhere=True)

        with self.assertRaises(Exception):
            dash.blacklist.update(self.ad_group, {'campaign': self.ad_group.campaign},
                                  BLACKLISTED, everywhere=True)

        with self.assertRaises(Exception):
            dash.blacklist.update(self.ad_group, {'account': self.ad_group.campaign.account},
                                  BLACKLISTED, everywhere=True)

    def test_global_blacklist(self):
        dash.blacklist.update(self.ad_group, {}, BLACKLISTED, self.domains, everywhere=True)
        self.assertEqual(
            set(dash.models.PublisherBlacklist.objects.filter(
                status=BLACKLISTED,
                everywhere=True
            ).values_list('name', flat=True)),
            set(self.domain_names + ['www.donaldjtrump.com'])
        )

    def test_global_blacklist_per_source(self):
        dash.blacklist.update(self.ad_group, {'source': self.source}, BLACKLISTED,
                              self.domains, everywhere=True)
        self.assertEqual(
            set(dash.models.PublisherBlacklist.objects.filter(
                everywhere=True,
                status=BLACKLISTED,
                source=self.source
            ).values_list('name', flat=True)),
            set(self.domain_names)
        )

    def test_global_blacklist_per_source_but_already_global(self):
        dash.blacklist.update(self.ad_group, {}, BLACKLISTED, self.domains, everywhere=True)
        dash.blacklist.update(self.ad_group, {'source': self.source}, BLACKLISTED,
                              self.domains, everywhere=True)
        self.assertEqual(
            set(),
            set(dash.models.PublisherBlacklist.objects.filter(
                everywhere=True,
                status=BLACKLISTED,
                source=self.source
            ).values_list('name', flat=True))
        )

    def test_global_enabling(self):
        dash.models.PublisherBlacklist.objects.create(
            name='www.google.com',
            everywhere=True
        )
        dash.models.PublisherBlacklist.objects.create(
            name='www.zemanta.com',
            everywhere=True
        )
        dash.blacklist.update(self.ad_group, {}, ENABLED, self.domains, everywhere=True)
        self.assertEqual(dash.models.PublisherBlacklist.objects.all().count(), 1)

    def test_global_enabling_per_source(self):
        dash.models.PublisherBlacklist.objects.create(
            name='www.google.com',
            everywhere=True
        )
        dash.models.PublisherBlacklist.objects.create(
            name='www.zemanta.com',
            source=self.source,
            everywhere=True
        )
        dash.blacklist.update(self.ad_group, {'source': self.source}, ENABLED,
                              self.domains, everywhere=True)
        self.assertEqual(
            set(dash.models.PublisherBlacklist.objects.all().values_list('name', flat=True)),
            set(['www.google.com', 'www.donaldjtrump.com'])
        )

    def test_account_blacklist(self):
        dash.blacklist.update(self.ad_group, {'source': self.source, 'account': self.account},
                              BLACKLISTED, self.domains)
        bl = dash.models.PublisherBlacklist.objects.filter(source=self.source,
                                                           status=BLACKLISTED,
                                                           account=self.account)
        self.assertEqual(set(bl.values_list('name', flat=True)), set(self.domain_names))

    def test_account_blacklist_ob_over_threshold(self):
        for i in range(dash.constants.MANUAL_ACTION_OUTBRAIN_BLACKLIST_THRESHOLD - 2):
            dash.models.PublisherBlacklist.objects.create(
                source=self.ob,
                name='www.page{}.com'.format(i),
                status=BLACKLISTED,
                account=self.account
            )

        dash.blacklist.update(self.ad_group, {'source': self.ob, 'account': self.account},
                              BLACKLISTED, self.domains)
        bl = dash.models.PublisherBlacklist.objects.filter(source=self.ob,
                                                           status=BLACKLISTED,
                                                           account=self.account)
        self.assertEqual(bl.count(), dash.constants.MANUAL_ACTION_OUTBRAIN_BLACKLIST_THRESHOLD + 1)

    def test_enable_blacklist_ob_over_threshold(self):
        for i in range(dash.constants.MANUAL_ACTION_OUTBRAIN_BLACKLIST_THRESHOLD + 5):
            dash.models.PublisherBlacklist.objects.create(
                source=self.ob,
                name='www.page{}.com'.format(i),
                status=BLACKLISTED,
                account=self.account
            )
        dash.models.PublisherBlacklist.objects.create(
            source=self.ob,
            name='www.google.com',
            status=BLACKLISTED,
            account=self.account
        )

        bl = dash.models.PublisherBlacklist.objects.filter(source=self.ob,
                                                           status=BLACKLISTED,
                                                           account=self.account)
        self.assertEqual(bl.count(), dash.constants.MANUAL_ACTION_OUTBRAIN_BLACKLIST_THRESHOLD + 6)

        dash.blacklist.update(self.ad_group, {'source': self.ob, 'account': self.account},
                              ENABLED, self.domains)
        bl = dash.models.PublisherBlacklist.objects.filter(source=self.ob,
                                                           status=BLACKLISTED,
                                                           account=self.account)
        self.assertEqual(bl.count(), dash.constants.MANUAL_ACTION_OUTBRAIN_BLACKLIST_THRESHOLD + 5)

    def test_enable_blacklist_ob_drop_under_threshold(self):
        for i in range(dash.constants.MANUAL_ACTION_OUTBRAIN_BLACKLIST_THRESHOLD + 1):
            dash.models.PublisherBlacklist.objects.create(
                source=self.ob,
                name='www.page{}.com'.format(i),
                status=BLACKLISTED,
                account=self.account
            )

        dash.blacklist.update(self.ad_group, {'source': self.ob, 'account': self.account}, ENABLED,
                              [
                                  ('www.page1.com', None),
                                  ('www.page2.com', None),
                                  ('www.page3.com', None),
                                  ('www.page4.com', None),
        ])
        bl = dash.models.PublisherBlacklist.objects.filter(source=self.ob,
                                                           status=BLACKLISTED,
                                                           account=self.account)
        self.assertEqual(bl.count(), dash.constants.MANUAL_ACTION_OUTBRAIN_BLACKLIST_THRESHOLD - 3)

        # No manual action should be present because we went under threshold

    def test_account_enabling(self):
        dash.models.PublisherBlacklist.objects.create(
            source=self.source,
            name='www.zemanta.com',
            status=BLACKLISTED,
            account=self.account
        )
        dash.models.PublisherBlacklist.objects.create(
            source=self.source,
            name='www.zemanata.com',
            status=BLACKLISTED,
            account=self.account
        )
        dash.blacklist.update(self.ad_group, {'source': self.source, 'account': self.account},
                              ENABLED, [('www.zemanata.com', None), ('www.google.com', None)])
        self.assertEqual(
            set(dash.models.PublisherBlacklist.objects.all().values_list('source', 'name')),
            set([
                (1, 'www.zemanta.com'),
                (None, 'www.donaldjtrump.com'),
            ])
        )

    def test_campaign_blacklist(self):
        dash.blacklist.update(self.ad_group, {'source': self.source, 'campaign': self.campaign},
                              BLACKLISTED, self.domains)
        self.assertEqual(
            set(dash.models.PublisherBlacklist.objects.all().values_list('source', 'name')),
            set([
                (1, 'www.zemanta.com'),
                (1, 'www.zemanata.com'),
                (1, 'www.google.com'),
                (None, 'www.donaldjtrump.com'),
            ])
        )

    def test_external_id(self):
        dash.blacklist.update(self.ad_group, {'source': self.source, 'account': self.account},
                              BLACKLISTED, self.domains)

        self.assertEqual(set(self.domains), set(
            (obj.name, obj.external_id) for obj in
            dash.models.PublisherBlacklist.objects.filter(source=self.source, account=self.account)
        ))

    def test_campaign_enabling(self):
        dash.models.PublisherBlacklist.objects.create(
            source=self.source,
            name='www.zemanta.com',
            status=BLACKLISTED,
            campaign=self.campaign
        )
        dash.models.PublisherBlacklist.objects.create(
            source=self.source,
            name='www.zemanata.com',
            status=BLACKLISTED,
            campaign=self.campaign
        )
        dash.blacklist.update(self.ad_group, {'source': self.source, 'campaign': self.campaign},
                              ENABLED, [('www.zemanata.com', None), ('www.google.com', None)])
        self.assertEqual(
            set(dash.models.PublisherBlacklist.objects.all().values_list('source', 'name')),
            set([
                (1, 'www.zemanta.com'),
                (None, 'www.donaldjtrump.com'),
            ])
        )

    @patch('utils.k1_helper.update_blacklist')
    def test_ad_group_blacklist(self, mock_k1_ping):
        dash.blacklist.update(self.ad_group, {'ad_group': self.ad_group, 'source': self.source},
                              BLACKLISTED, self.domains)
        self.assertEqual(
            set(dash.models.PublisherBlacklist.objects.all().values_list('source', 'name')),
            set([
                (1, u'www.google.com'),
                (1, u'www.zemanta.com'),
                (1, u'www.zemanata.com'),
                (None, 'www.donaldjtrump.com'),
            ])
        )
        mock_k1_ping.assert_called_with(1, msg='blacklist.update')

    @patch('utils.k1_helper.update_blacklist')
    def test_ad_group_blacklist_all_sources(self, mock_k1_ping):
        dash.blacklist.update(self.ad_group, {'ad_group': self.ad_group}, BLACKLISTED, self.domains,
                              all_sources=True)
        self.assertEqual(
            set(dash.models.PublisherBlacklist.objects.all().values_list('source', 'name')),
            set([
                (1, u'www.google.com'),
                (1, u'www.zemanta.com'),
                (1, u'www.zemanata.com'),
                (7, u'www.google.com'),
                (7, u'www.zemanta.com'),
                (7, u'www.zemanata.com'),
                (None, 'www.donaldjtrump.com'),
            ])
        )
        mock_k1_ping.assert_called_with(1, msg='blacklist.update')

    @patch('utils.k1_helper.update_blacklist')
    def test_ad_group_blacklist_all_b1_sources(self, mock_k1_ping):
        dash.blacklist.update(self.ad_group, {'ad_group': self.ad_group}, BLACKLISTED, self.domains,
                              all_b1_sources=True)
        self.assertEqual(
            set(dash.models.PublisherBlacklist.objects.all().values_list('source', 'name')),
            set([
                (None, u'www.google.com'),
                (None, u'www.zemanta.com'),
                (None, u'www.zemanata.com'),
                (None, u'www.donaldjtrump.com'),
            ])
        )
        mock_k1_ping.assert_called_with(1, msg='blacklist.update')

    def test_ad_group_blacklist_wrong_constrains(self):
        with self.assertRaises(Exception) as msg1:
            dash.blacklist.update(self.ad_group,
                                  {'ad_group': self.ad_group, 'account': self.account},
                                  BLACKLISTED,
                                  self.domains
                                  )
        self.assertEqual(
            str(msg1.exception),
            'You must use exactly one of the following_constraints: ad_group, campaign, account'
        )
        with self.assertRaises(Exception) as msg2:
            dash.blacklist.update(self.ad_group,
                                  {'ad_group': self.ad_group, 'campaign': self.campaign},
                                  BLACKLISTED,
                                  self.domains
                                  )
        self.assertEqual(
            str(msg2.exception),
            'You must use exactly one of the following_constraints: ad_group, campaign, account'
        )

    @patch('utils.k1_helper.update_blacklist')
    def test_ad_group_enabling(self, mock_k1_ping):
        dash.models.PublisherBlacklist.objects.create(
            ad_group=self.ad_group,
            status=BLACKLISTED,
            source=self.source,
            name='www.zemanta.com'
        )
        dash.blacklist.update(self.ad_group, {'ad_group': self.ad_group, 'source': self.source},
                              ENABLED, self.domains)
        mock_k1_ping.assert_called_with(1, msg='blacklist.update')
        self.assertEqual(dash.models.PublisherBlacklist.objects.all().count(), 1)

        mock_k1_ping.reset_mock()
        dash.blacklist.update(self.ad_group, {'ad_group': self.ad_group, 'source': self.source},
                              ENABLED, self.domains)
        self.assertEqual(dash.models.PublisherBlacklist.objects.all().count(), 1)
        mock_k1_ping.assert_called_with(1, msg='blacklist.update')
