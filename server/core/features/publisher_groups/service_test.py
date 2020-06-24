import csv
import io
import textwrap

import mock
from django.http.request import HttpRequest
from django.test import override_settings

import zemauth.models
from core.common.base_test_case import CoreTestCase
from core.common.base_test_case import FutureCoreTestCase
from dash import constants
from dash import history_helpers
from dash import models
from utils import test_helper
from utils.magic_mixer import get_request_mock
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission

from . import connection_definitions
from . import csv_helper
from . import exceptions
from . import service


class LegacyPublisherGroupHelpersTestCase(CoreTestCase):
    fixtures = ["test_publishers.yaml"]

    def setUp(self):
        self.request = HttpRequest()
        self.request.user = zemauth.models.User.objects.get(id=2)

    def assertEntriesEqual(self, publisher_group, entries):
        self.assertCountEqual(
            publisher_group.entries.all().values("publisher", "include_subdomains", "source"), entries
        )

    def assertWhitelistCreated(self, obj):
        self.assertIsNotNone(obj.default_whitelist)
        self.assertEqual(obj.default_whitelist.name, obj.get_default_whitelist_name())
        self.assertEqual(obj.get_account(), obj.default_whitelist.account)
        self.assertTrue(obj.default_whitelist.implicit)

    def assertBlacklistCreated(self, obj):
        self.assertIsNotNone(obj.default_blacklist)
        self.assertEqual(obj.default_blacklist.name, obj.get_default_blacklist_name())
        self.assertEqual(obj.get_account(), obj.default_blacklist.account)
        self.assertTrue(obj.default_blacklist.implicit)

    def assertHistoryNotWritten(self, history):
        self.assertEqual(history.count(), 0)

    def assertHistoryWritten(self, history, changes_text, default_list_created):
        self.assertEqual(history.count(), 2 if default_list_created else 1)
        self.assertEqual(history.first().changes_text, changes_text)

    @mock.patch("core.features.publisher_groups.service._ping_k1")
    @mock.patch("utils.email_helper.send_obj_changes_notification_email")
    def test_blacklist_publisher_ad_group(self, mock_email, mock_k1_ping):
        obj = models.AdGroup.objects.get(pk=1)
        service.blacklist_publishers(
            self.request, [{"publisher": "cnn.com", "source": None, "include_subdomains": False}], obj
        )

        self.assertEntriesEqual(
            obj.default_blacklist, [{"publisher": "cnn.com", "source": None, "include_subdomains": False}]
        )

        changes_text = "Blacklisted the following publishers on ad group level: cnn.com on all sources."
        mock_email.assert_called_with(obj, self.request, changes_text)
        self.assertHistoryWritten(history_helpers.get_ad_group_history(obj), changes_text, False)
        mock_k1_ping.assert_not_called()

    @mock.patch("core.features.publisher_groups.service._ping_k1")
    @mock.patch("utils.email_helper.send_obj_changes_notification_email")
    def test_blacklist_publisher_ad_group_no_history(self, mock_email, mock_k1_ping):
        obj = models.AdGroup.objects.get(pk=1)
        service.blacklist_publishers(
            self.request,
            [{"publisher": "cnn.com", "source": None, "include_subdomains": False}],
            obj,
            should_write_history=False,
        )

        self.assertEntriesEqual(
            obj.default_blacklist, [{"publisher": "cnn.com", "source": None, "include_subdomains": False}]
        )

        mock_email.assert_not_called()
        self.assertHistoryNotWritten(history_helpers.get_ad_group_history(obj))
        mock_k1_ping.assert_not_called()

    @mock.patch("core.features.publisher_groups.service._ping_k1")
    @mock.patch("utils.email_helper.send_obj_changes_notification_email")
    def test_whitelist_publisher_ad_group(self, mock_email, mock_k1_ping):
        obj = models.AdGroup.objects.get(pk=1)
        service.whitelist_publishers(
            self.request, [{"publisher": "cnn.com", "source": None, "include_subdomains": False}], obj
        )

        self.assertEntriesEqual(
            obj.default_whitelist, [{"publisher": "cnn.com", "source": None, "include_subdomains": False}]
        )
        changes_text = "Whitelisted the following publishers on ad group level: cnn.com on all sources."
        mock_email.assert_called_with(obj, self.request, changes_text)
        self.assertHistoryWritten(history_helpers.get_ad_group_history(obj), changes_text, False)
        mock_k1_ping.assert_not_called()

    @mock.patch("core.features.publisher_groups.service._ping_k1")
    @mock.patch("utils.email_helper.send_obj_changes_notification_email")
    def test_whitelist_publisher_ad_group_no_history(self, mock_email, mock_k1_ping):
        obj = models.AdGroup.objects.get(pk=1)
        service.whitelist_publishers(
            self.request,
            [{"publisher": "cnn.com", "source": None, "include_subdomains": False}],
            obj,
            should_write_history=False,
        )

        self.assertEntriesEqual(
            obj.default_whitelist, [{"publisher": "cnn.com", "source": None, "include_subdomains": False}]
        )
        mock_email.assert_not_called()
        self.assertHistoryNotWritten(history_helpers.get_ad_group_history(obj))

    @mock.patch("utils.k1_helper.update_ad_group")
    def test_blacklist_publisher_ad_group_k1_ping(self, mock_k1_ping):
        obj = magic_mixer.blend(models.AdGroup, default_blacklist=None)
        self.assertIsNone(obj.default_blacklist)

        service.blacklist_publishers(
            self.request, [{"publisher": "cnn.com", "source": None, "include_subdomains": False}], obj
        )
        self.assertBlacklistCreated(obj)
        mock_k1_ping.assert_called_once_with(obj, "publisher_group.create")

    @mock.patch("utils.k1_helper.update_ad_group")
    def test_whitelist_publisher_ad_group_k1_ping(self, mock_k1_ping):
        obj = magic_mixer.blend(models.AdGroup, default_whitelist=None)
        self.assertIsNone(obj.default_whitelist)

        service.whitelist_publishers(
            self.request, [{"publisher": "cnn.com", "source": None, "include_subdomains": False}], obj
        )
        self.assertWhitelistCreated(obj)
        mock_k1_ping.assert_called_once_with(obj, "publisher_group.create")

    @mock.patch("core.features.publisher_groups.service._ping_k1")
    @mock.patch("utils.email_helper.send_obj_changes_notification_email")
    def test_unlist_whitelisted_publisher_ad_group(self, mock_email, mock_k1_ping):
        obj = models.AdGroup.objects.get(pk=1)
        models.PublisherGroupEntry.objects.create(
            publisher_group=obj.default_whitelist, source=None, publisher="cnn.com"
        )
        self.assertEntriesEqual(
            obj.default_whitelist, [{"publisher": "cnn.com", "source": None, "include_subdomains": True}]
        )

        service.unlist_publishers(self.request, [{"publisher": "cnn.com", "source": None}], obj)
        self.assertEntriesEqual(obj.default_whitelist, [])

        changes_text = "Disabled the following publishers on ad group level: cnn.com on all sources."
        mock_email.assert_called_with(obj, self.request, changes_text)
        self.assertHistoryWritten(history_helpers.get_ad_group_history(obj), changes_text, False)
        mock_k1_ping.assert_not_called()

    @mock.patch("core.features.publisher_groups.service._ping_k1")
    @mock.patch("utils.email_helper.send_obj_changes_notification_email")
    def test_unlist_blacklisted_publisher_ad_group(self, mock_email, mock_k1_ping):
        obj = models.AdGroup.objects.get(pk=1)
        models.PublisherGroupEntry.objects.create(
            publisher_group=obj.default_blacklist, source=None, publisher="cnn.com"
        )
        self.assertEntriesEqual(
            obj.default_blacklist, [{"publisher": "cnn.com", "source": None, "include_subdomains": True}]
        )

        service.unlist_publishers(self.request, [{"publisher": "cnn.com", "source": None}], obj)
        self.assertEntriesEqual(obj.default_blacklist, [])

        changes_text = "Enabled the following publishers on ad group level: cnn.com on all sources."
        mock_email.assert_called_with(obj, self.request, changes_text)
        self.assertHistoryWritten(history_helpers.get_ad_group_history(obj), changes_text, False)
        mock_k1_ping.assert_not_called()

    @mock.patch("core.models.Campaign.adgroup_set")
    @mock.patch("utils.k1_helper.update_ad_groups")
    @mock.patch("utils.email_helper.send_obj_changes_notification_email")
    def test_blacklist_publisher_campaign(self, mock_email, mock_k1_ping, mock_queryset):
        mock_queryset.filter_active.return_value.exclude_archived.return_value = ["ad_group"]

        obj = models.Campaign.objects.get(pk=1)
        self.assertIsNone(obj.default_blacklist)

        service.blacklist_publishers(
            self.request, [{"publisher": "cnn.com", "source": None, "include_subdomains": False}], obj
        )

        self.assertEntriesEqual(
            obj.default_blacklist, [{"publisher": "cnn.com", "source": None, "include_subdomains": False}]
        )
        self.assertBlacklistCreated(obj)

        changes_text = "Blacklisted the following publishers on campaign level: cnn.com on all sources."
        mock_email.assert_called_with(obj, self.request, changes_text)
        self.assertHistoryWritten(history_helpers.get_campaign_history(obj), changes_text, False)
        mock_k1_ping.assert_called_once_with(["ad_group"], "publisher_group.create")

    @mock.patch("core.models.Campaign.adgroup_set")
    @mock.patch("utils.k1_helper.update_ad_groups")
    @mock.patch("utils.email_helper.send_obj_changes_notification_email")
    def test_whitelist_publisher_campaign(self, mock_email, mock_k1_ping, mock_queryset):
        mock_queryset.filter_active.return_value.exclude_archived.return_value = ["ad_group"]

        obj = models.Campaign.objects.get(pk=1)
        self.assertIsNone(obj.default_whitelist)

        service.whitelist_publishers(
            self.request, [{"publisher": "cnn.com", "source": None, "include_subdomains": False}], obj
        )

        self.assertEntriesEqual(
            obj.default_whitelist, [{"publisher": "cnn.com", "source": None, "include_subdomains": False}]
        )
        self.assertWhitelistCreated(obj)

        changes_text = "Whitelisted the following publishers on campaign level: cnn.com on all sources."
        mock_email.assert_called_with(obj, self.request, changes_text)
        self.assertHistoryWritten(history_helpers.get_campaign_history(obj), changes_text, False)
        mock_k1_ping.assert_called_once_with(["ad_group"], "publisher_group.create")

    @mock.patch("core.features.publisher_groups.service._ping_k1")
    @mock.patch("utils.email_helper.send_obj_changes_notification_email")
    def test_unlist_whitelisted_publisher_campaign(self, mock_email, mock_k1_ping):
        obj = models.Campaign.objects.get(pk=1)
        publisher_group = models.PublisherGroup(name="was")
        publisher_group.save(self.request)

        obj.default_whitelist = publisher_group
        obj.save(self.request)

        models.PublisherGroupEntry.objects.create(
            publisher_group=obj.default_whitelist, source=None, publisher="cnn.com"
        )
        self.assertEntriesEqual(
            obj.default_whitelist, [{"publisher": "cnn.com", "source": None, "include_subdomains": True}]
        )

        service.unlist_publishers(self.request, [{"publisher": "cnn.com", "source": None}], obj)
        self.assertEntriesEqual(obj.default_whitelist, [])

        changes_text = "Disabled the following publishers on campaign level: cnn.com on all sources."
        mock_email.assert_called_with(obj, self.request, changes_text)
        self.assertHistoryWritten(history_helpers.get_campaign_history(obj), changes_text, False)
        mock_k1_ping.assert_not_called()

    @mock.patch("core.features.publisher_groups.service._ping_k1")
    @mock.patch("utils.email_helper.send_obj_changes_notification_email")
    def test_unlist_blacklisted_publisher_campaign(self, mock_email, mock_k1_ping):
        obj = models.Campaign.objects.get(pk=1)
        publisher_group = models.PublisherGroup(name="was")
        publisher_group.save(self.request)

        obj.default_blacklist = publisher_group
        obj.save(self.request)

        models.PublisherGroupEntry.objects.create(
            publisher_group=obj.default_blacklist, source=None, publisher="cnn.com"
        )
        self.assertEntriesEqual(
            obj.default_blacklist, [{"publisher": "cnn.com", "source": None, "include_subdomains": True}]
        )

        service.unlist_publishers(self.request, [{"publisher": "cnn.com", "source": None}], obj)
        self.assertEntriesEqual(obj.default_blacklist, [])

        changes_text = "Enabled the following publishers on campaign level: cnn.com on all sources."
        mock_email.assert_called_with(obj, self.request, changes_text)
        self.assertHistoryWritten(history_helpers.get_campaign_history(obj), changes_text, False)
        mock_k1_ping.assert_not_called()

    @mock.patch("core.models.AdGroup.objects")
    @mock.patch("utils.k1_helper.update_ad_groups")
    @mock.patch("utils.email_helper.send_obj_changes_notification_email")
    def test_blacklist_publisher_account(self, mock_email, mock_k1_ping, mock_queryset):
        mock_queryset.filter.return_value.filter_active.return_value.exclude_archived.return_value = ["ad_group"]

        obj = models.Account.objects.get(pk=1)

        service.blacklist_publishers(
            self.request, [{"publisher": "cnn.com", "source": None, "include_subdomains": False}], obj
        )

        self.assertEntriesEqual(
            obj.default_blacklist, [{"publisher": "cnn.com", "source": None, "include_subdomains": False}]
        )
        self.assertBlacklistCreated(obj)

        changes_text = "Blacklisted the following publishers on account level: cnn.com on all sources."
        mock_email.assert_called_with(obj, self.request, changes_text)
        self.assertHistoryWritten(history_helpers.get_account_history(obj), changes_text, False)

        self.assertEqual(models.CpcConstraint.objects.all().count(), 0)
        mock_k1_ping.assert_called_once_with(["ad_group"], "publisher_group.create")

    @mock.patch("utils.email_helper.send_obj_changes_notification_email")
    def test_limit_outbrain_blacklist(self, mock_email):
        obj = models.Account.objects.get(pk=1000)
        outbrain = models.Source.objects.get(pk=3)
        for i in range(service.OUTBRAIN_MAX_BLACKLISTED_PUBLISHERS):
            models.PublisherGroupEntry.objects.create(
                publisher_group=obj.default_blacklist, source=outbrain, publisher="cnn{}.com".format(i)
            )
        non_relevant_entries = [
            {"publisher": "cnn{}.com".format(x), "source": None, "include_subdomains": False} for x in range(10)
        ]
        ob_entries = [{"publisher": "cnn.com", "source": outbrain, "include_subdomains": False}]

        with self.assertRaises(exceptions.PublisherGroupTargetingException):
            service.blacklist_publishers(self.request, ob_entries + non_relevant_entries, obj)

    @mock.patch("core.models.AdGroup.objects")
    @mock.patch("utils.k1_helper.update_ad_groups")
    @mock.patch("utils.email_helper.send_obj_changes_notification_email")
    def test_whitelist_publisher_account(self, mock_email, mock_k1_ping, mock_queryset):
        mock_queryset.filter.return_value.filter_active.return_value.exclude_archived.return_value = ["ad_group"]

        obj = models.Account.objects.get(pk=1)
        service.whitelist_publishers(
            self.request, [{"publisher": "cnn.com", "source": None, "include_subdomains": False}], obj
        )

        self.assertEntriesEqual(
            obj.default_whitelist, [{"publisher": "cnn.com", "source": None, "include_subdomains": False}]
        )
        self.assertWhitelistCreated(obj)

        changes_text = "Whitelisted the following publishers on account level: cnn.com on all sources."
        mock_email.assert_called_with(obj, self.request, changes_text)
        self.assertHistoryWritten(history_helpers.get_account_history(obj), changes_text, False)
        mock_k1_ping.assert_called_once_with(["ad_group"], "publisher_group.create")

    @mock.patch("core.features.publisher_groups.service._ping_k1")
    @mock.patch("utils.email_helper.send_obj_changes_notification_email")
    def test_unlist_whitelisted_publisher_account(self, mock_email, mock_k1_ping):
        obj = models.Account.objects.get(pk=1)
        publisher_group = models.PublisherGroup(name="was")
        publisher_group.save(self.request)

        obj.default_whitelist = publisher_group
        obj.save(self.request)

        models.PublisherGroupEntry.objects.create(
            publisher_group=obj.default_whitelist, source=None, publisher="cnn.com"
        )

        service.unlist_publishers(
            self.request, [{"publisher": "cnn.com", "source": None, "include_subdomains": False}], obj
        )
        self.assertEntriesEqual(obj.default_whitelist, [])

        changes_text = "Disabled the following publishers on account level: cnn.com on all sources."
        mock_email.assert_called_with(obj, self.request, changes_text)
        self.assertHistoryWritten(history_helpers.get_account_history(obj), changes_text, False)
        mock_k1_ping.assert_not_called()

    @mock.patch("core.features.publisher_groups.service._ping_k1")
    @mock.patch("utils.email_helper.send_obj_changes_notification_email")
    def test_blacklist_publisher_global(self, mock_email, mock_k1_ping):
        global_group = models.PublisherGroup(name="imglobal")
        global_group.save(self.request)

        with override_settings(GLOBAL_BLACKLIST_ID=global_group.id):
            service.blacklist_publishers(
                self.request, [{"publisher": "cnn.com", "source": None, "include_subdomains": False}], None
            )

            self.assertEntriesEqual(
                global_group, [{"publisher": "cnn.com", "source": None, "include_subdomains": False}]
            )
        self.assertFalse(mock_email.called)
        mock_k1_ping.assert_not_called()

    @mock.patch("core.features.publisher_groups.service._ping_k1")
    @mock.patch("utils.email_helper.send_obj_changes_notification_email")
    def test_whitelist_publisher_global(self, mock_email, mock_k1_ping):
        with self.assertRaises(exceptions.PublisherGroupTargetingException):
            # not available
            service.whitelist_publishers(
                self.request, [{"publisher": "cnn.com", "source": None, "include_subdomains": False}], None
            )
            self.assertFalse(mock_email.called)
            mock_k1_ping.assert_not_called()

    @mock.patch("core.features.publisher_groups.service._ping_k1")
    @mock.patch("utils.email_helper.send_obj_changes_notification_email")
    def test_unlist_publisher_global(self, mock_email, mock_k1_ping):
        global_group = models.PublisherGroup(name="imglobal")
        global_group.save(self.request)

        models.PublisherGroupEntry.objects.create(publisher_group=global_group, source=None, publisher="cnn.com")

        with override_settings(GLOBAL_BLACKLIST_ID=global_group.id):
            service.unlist_publishers(
                self.request, [{"publisher": "cnn.com", "source": None, "include_subdomains": False}], None
            )

            self.assertEntriesEqual(global_group, [])
        self.assertFalse(mock_email.called)
        mock_k1_ping.assert_not_called()

    def test_concat_publisher_targeting(self):
        ad_group = models.AdGroup.objects.get(pk=1)
        ad_group_settings = ad_group.get_current_settings()
        campaign = models.Campaign.objects.get(pk=1)
        campaign_settings = campaign.get_current_settings()
        account = models.Account.objects.get(pk=1)
        account_settings = account.get_current_settings()
        agency = models.Agency.objects.get(pk=1)
        agency_settings = agency.get_current_settings()

        with override_settings(GLOBAL_BLACKLIST_ID=1):
            ad_group.default_blacklist_id = 2
            ad_group_settings.blacklist_publisher_groups = [3]
            campaign.default_blacklist_id = 4
            campaign_settings.blacklist_publisher_groups = [5]
            account.default_blacklist_id = 6
            account_settings.blacklist_publisher_groups = [7]
            agency.default_blacklist_id = 8
            agency_settings.blacklist_publisher_groups = [9]

            ad_group.default_whitelist_id = 11
            ad_group_settings.whitelist_publisher_groups = [12]
            campaign.default_whitelist_id = 13
            campaign_settings.whitelist_publisher_groups = [14]
            account.default_whitelist_id = 15
            account_settings.whitelist_publisher_groups = [16]
            agency.default_whitelist_id = 17
            agency_settings.whitelist_publisher_groups = [18]

            blacklist, whitelist = service.concat_publisher_group_targeting(
                ad_group,
                ad_group_settings,
                campaign,
                campaign_settings,
                account,
                account_settings,
                agency,
                agency_settings,
            )

        self.assertEqual(blacklist, [1, 2, 3, 4, 5, 6, 7, 8, 9])
        self.assertEqual(whitelist, [11, 12, 13, 14, 15, 16, 17, 18])

    def test_blacklist_outbrain_validation(self):
        outbrain = models.Source.objects.get(pk=3)

        obj = models.Account.objects.get(pk=1)
        entries = [{"publisher": "cnn.com", "source": outbrain, "include_subdomains": False}]

        service.blacklist_publishers(self.request, entries, obj)  # no error

        with self.assertRaisesMessage(Exception, "Outbrain specific blacklisting is only available on account level"):
            service.blacklist_publishers(self.request, entries, models.Campaign.objects.get(pk=1))

        with self.assertRaisesMessage(Exception, "Outbrain specific blacklisting is only available on account level"):
            service.blacklist_publishers(self.request, entries, models.AdGroup.objects.get(pk=1))

        with self.assertRaisesMessage(Exception, "Outbrain specific blacklisting is only available on account level"):
            service.blacklist_publishers(self.request, entries, None)

    def test_upsert_publisher_group_update(self):
        form_data = {"id": 1, "name": "Bla bla bla", "include_subdomains": False, "account_id": 1}

        publisher_group = service.upsert_publisher_group(self.request, form_data, None)
        publisher_group.refresh_from_db()

        self.assertEqual(
            form_data,
            {
                "id": publisher_group.id,
                "account_id": publisher_group.account.id,
                "name": publisher_group.name,
                "include_subdomains": publisher_group.default_include_subdomains,
            },
        )

        self.assertEqual(
            models.History.objects.last().changes_text,
            'Publisher group "pg 1 [1]" updated, name changed from "pg 1" to "Bla bla bla", '
            'subdomains included changed from "True" to "False"',
        )

    def test_upsert_publisher_group_create(self):
        form_data = {"name": "Bla bla bla", "include_subdomains": False}

        publisher_group = service.upsert_publisher_group(self.request, form_data, None)
        publisher_group.refresh_from_db()

        self.assertEqual(
            form_data, {"name": publisher_group.name, "include_subdomains": publisher_group.default_include_subdomains}
        )


class PublisherGroupHelpersTestCase(FutureCoreTestCase, LegacyPublisherGroupHelpersTestCase):
    pass


class PublisherGroupCSVHelpersTestCase(FutureCoreTestCase):
    fixtures = ["test_publishers.yaml"]

    def test_get_csv_content(self):
        publisher_group = models.PublisherGroup.objects.get(pk=1)
        self.assertEqual(
            csv_helper.get_csv_content(publisher_group.entries.all(), account=publisher_group.account),
            textwrap.dedent(
                """\
            "Publisher","Placement","Source"\r
            "pub1","plac1","adsnative"\r
            "pub2","",""\r
            """
            ),
        )

    def test_get_csv_content_outbrain_publisher_id(self):
        publisher_group = models.PublisherGroup.objects.get(pk=1)
        publisher_group.account.agency.id = 55
        self.assertEqual(
            csv_helper.get_csv_content(publisher_group.entries.all(), account=publisher_group.account),
            textwrap.dedent(
                """\
            "Publisher","Placement","Source","Outbrain Publisher Id","Outbrain Section Id","Outbrain Amplify Publisher Id","Outbrain Engage Publisher Id"\r
            "pub1","plac1","adsnative","","","",""\r
            "pub2","","","asd123","asd1234","asd12345","df164"\r
            """
            ),
        )

    def test_get_csv_content_all_cases_without_placement(self):
        agency = magic_mixer.blend(models.Agency)
        account = magic_mixer.blend(models.Account, agency=agency)
        source = magic_mixer.blend(models.Source, bidder_slug="somesource")
        publisher_group = magic_mixer.blend(models.PublisherGroup, account=account)
        publisher_group_entries = [
            magic_mixer.blend(models.PublisherGroupEntry, publisher_group=publisher_group, publisher="example.com"),
            magic_mixer.blend(
                models.PublisherGroupEntry, publisher_group=publisher_group, publisher="example.com", source=source
            ),
        ]

        rows = [
            row
            for row in csv.DictReader(
                io.StringIO(csv_helper.get_csv_content(publisher_group.entries.all(), account=publisher_group.account))
            )
        ]
        self.assertEqual(
            set(tuple(row.items()) for row in rows),
            {
                (
                    ("Publisher", e.publisher if e.publisher is not None else ""),
                    ("Source", e.source.bidder_slug if e.source is not None else ""),
                )
                for e in publisher_group_entries
            },
        )

    def test_get_csv_content_all_cases_without_placement_existing_placement_entry(self):
        agency = magic_mixer.blend(models.Agency)
        account = magic_mixer.blend(models.Account, agency=agency)
        source = magic_mixer.blend(models.Source, bidder_slug="somesource")
        publisher_group = magic_mixer.blend(models.PublisherGroup, account=account)
        publisher_group_entries = [
            magic_mixer.blend(models.PublisherGroupEntry, publisher_group=publisher_group, publisher="example.com"),
            magic_mixer.blend(
                models.PublisherGroupEntry, publisher_group=publisher_group, publisher="example.com", source=source
            ),
            magic_mixer.blend(
                models.PublisherGroupEntry,
                publisher_group=publisher_group,
                publisher="example.com",
                source=source,
                placement="someplacement",
            ),
            magic_mixer.blend(
                models.PublisherGroupEntry,
                publisher_group=publisher_group,
                publisher="example.com",
                placement="someplacement",
            ),
        ]
        rows = [
            row
            for row in csv.DictReader(
                io.StringIO(csv_helper.get_csv_content(publisher_group.entries.all(), account=publisher_group.account))
            )
        ]
        self.assertEqual(
            set(tuple(row.items()) for row in rows),
            {
                (
                    ("Publisher", e.publisher if e.publisher is not None else ""),
                    ("Placement", e.placement if e.placement is not None else ""),
                    ("Source", e.source.bidder_slug if e.source is not None else ""),
                )
                for e in publisher_group_entries
            },
        )

    def test_get_csv_content_all_cases_with_placement(self):
        agency = magic_mixer.blend(models.Agency)
        account = magic_mixer.blend(models.Account, agency=agency)
        source = magic_mixer.blend(models.Source, bidder_slug="somesource")
        publisher_group = magic_mixer.blend(models.PublisherGroup, account=account)
        publisher_group_entries = [
            magic_mixer.blend(models.PublisherGroupEntry, publisher_group=publisher_group, publisher="example.com"),
            magic_mixer.blend(
                models.PublisherGroupEntry, publisher_group=publisher_group, publisher="example.com", source=source
            ),
            magic_mixer.blend(
                models.PublisherGroupEntry,
                publisher_group=publisher_group,
                publisher="example.com",
                source=source,
                placement="someplacement",
            ),
            magic_mixer.blend(
                models.PublisherGroupEntry,
                publisher_group=publisher_group,
                publisher="example.com",
                placement="someplacement",
            ),
        ]

        rows = [
            row
            for row in csv.DictReader(
                io.StringIO(
                    csv_helper.get_csv_content(
                        publisher_group.entries.all(), include_placement=True, account=publisher_group.account
                    )
                )
            )
        ]
        self.assertEqual(
            set(tuple(row.items()) for row in rows),
            {
                (
                    ("Publisher", e.publisher if e.publisher is not None else ""),
                    ("Placement", e.placement if e.placement is not None else ""),
                    ("Source", e.source.bidder_slug if e.source is not None else ""),
                )
                for e in publisher_group_entries
            },
        )

    def test_get_example_csv_content_without_placement(self):
        rows = [row for row in csv.DictReader(io.StringIO(csv_helper.get_example_csv_content()))]
        self.assertEqual(
            set(tuple(row.items()) for row in rows),
            {
                (("Publisher", "example.com"), ("Source (optional)", "")),
                (("Publisher", "some.example.com"), ("Source (optional)", "")),
            },
        )

    def test_get_example_csv_content_with_placement(self):
        rows = [row for row in csv.DictReader(io.StringIO(csv_helper.get_example_csv_content(include_placement=True)))]
        self.assertEqual(
            set(tuple(row.items()) for row in rows),
            {
                (("Publisher", "example.com"), ("Placement (optional)", ""), ("Source (optional)", "")),
                (("Publisher", "some.example.com"), ("Placement (optional)", ""), ("Source (optional)", "")),
            },
        )

    def test_validate_entries(self):
        self.assertEqual(
            csv_helper.validate_entries(
                [
                    {"publisher": "wwwpub1.com", "source": "AdsNative", "include_subdomains": True},
                    {"publisher": "https://pub1.com", "source": "", "include_subdomains": True},
                    {"publisher": "https://pub1.com", "source": "asd", "include_subdomains": False},
                    {"publisher": "pub2.com", "include_subdomains": False},
                ]
            ),
            [
                {"publisher": "wwwpub1.com", "source": "AdsNative", "include_subdomains": True},
                {
                    "publisher": "https://pub1.com",
                    "source": None,
                    "include_subdomains": True,
                    "error": "Remove the following prefixes: http, https",
                },
                {
                    "publisher": "https://pub1.com",
                    "source": "asd",
                    "include_subdomains": False,
                    "error": "Remove the following prefixes: http, https; Unknown source",
                },
                {"publisher": "pub2.com", "include_subdomains": False, "source": None},
            ],
        )

    def test_validate_entries_with_error(self):
        self.assertEqual(
            csv_helper.validate_entries(
                [
                    {"publisher": "wwwpub1.com", "source": "AdsNative", "include_subdomains": True},
                    {
                        "publisher": "pub1.com",
                        "source": "",
                        "include_subdomains": True,
                        "error": "Remove the following prefixes: http, https",
                    },
                    {
                        "publisher": "https://pub1.com",
                        "source": "asd",
                        "include_subdomains": False,
                        "error": "Remove the following prefixes: http, https; Unknown source",
                    },
                ]
            ),
            [
                {"publisher": "wwwpub1.com", "source": "AdsNative", "include_subdomains": True},
                {"publisher": "pub1.com", "source": None, "include_subdomains": True},
                {
                    "publisher": "https://pub1.com",
                    "source": "asd",
                    "include_subdomains": False,
                    "error": "Remove the following prefixes: http, https; Unknown source",
                },
            ],
        )

    def test_clean_entry_sources(self):
        entries = [
            {"publisher": "pub1.com", "source": "AdsNative", "include_subdomains": True},
            {"publisher": "https://pub1.com", "source": "", "include_subdomains": True},
            {"publisher": "https://pub2.com", "source": "adsnative", "include_subdomains": True},
            {"publisher": "https://pub3.com", "include_subdomains": True},
        ]

        csv_helper.clean_entry_sources(entries)

        self.assertEqual(
            entries,
            [
                {"publisher": "pub1.com", "source": models.Source.objects.get(pk=1), "include_subdomains": True},
                {"publisher": "https://pub1.com", "source": None, "include_subdomains": True},
                {
                    "publisher": "https://pub2.com",
                    "source": models.Source.objects.get(pk=1),
                    "include_subdomains": True,
                },
                {"publisher": "https://pub3.com", "source": None, "include_subdomains": True},
            ],
        )

    def test_get_entries_errors_csv_content(self):
        entries = [
            {
                "publisher": "pub1",
                "source": models.Source.objects.get(pk=1).name,
                "include_subdomains": True,
                "outbrain_publisher_id": "12345",
                "outbrain_section_id": "123456",
                "outbrain_amplify_publisher_id": "1234567",
                "outbrain_engage_publisher_id": "12345678",
            },
            {"publisher": "pub2", "source": None, "include_subdomains": True},
        ]
        account = models.Account.objects.get(pk=1)
        account.agency.id = 55
        self.assertEqual(
            csv_helper.get_entries_errors_csv_content(entries, account=account),
            textwrap.dedent(
                """\
            "Publisher","Source","Outbrain Publisher Id","Outbrain Section Id","Outbrain Amplify Publisher Id","Outbrain Engage Publisher Id","Error"\r
            "pub1","AdsNative","12345","123456","1234567","12345678",""\r
            "pub2","","","","","",""\r
            """
            ),
        )


class LegacyGetOrCreatePublisherGroupTestCase(CoreTestCase):
    def setUp(self):
        super().setUp()
        self.request = get_request_mock(self.user)
        self.account = self.mix_account(self.request.user, permissions=[Permission.READ, Permission.WRITE])
        self.agency = self.mix_agency(self.request.user, permissions=[Permission.READ, Permission.WRITE])
        self.other_account = magic_mixer.blend(models.Account)
        self.publisher_group = magic_mixer.blend(models.PublisherGroup, account=self.account)
        self.other_publisher_group = magic_mixer.blend(models.PublisherGroup, account=self.other_account)

    def test_get_existing_publisher_group(self):
        publisher_group, created = service.get_or_create_publisher_group(
            self.request,
            self.publisher_group.name,
            publisher_group_id=self.publisher_group.id,
            account_id=self.account.id,
            default_include_subdomains=self.publisher_group.default_include_subdomains,
        )

        self.assertFalse(created)
        self.assertEqual(publisher_group, self.publisher_group)

    def test_create_new_publisher_group(self):
        pg_name = "somerandomname"
        self.assertEqual(models.PublisherGroup.objects.filter(name=pg_name).count(), 0)
        publisher_group, created = service.get_or_create_publisher_group(
            self.request, pg_name, publisher_group_id=None, account_id=self.account.id, default_include_subdomains=True
        )

        self.assertTrue(created)
        self.assertEqual(publisher_group.name, pg_name)
        self.assertIsNone(publisher_group.agency)
        self.assertEqual(publisher_group.account, self.account)
        self.assertTrue(publisher_group.default_include_subdomains)
        self.assertFalse(publisher_group.implicit)
        self.assertEqual(models.PublisherGroup.objects.filter(name=pg_name).count(), 1)

    def test_no_access_to_foreign_publisher_group(self):
        with self.assertRaises(models.PublisherGroup.DoesNotExist):
            service.get_or_create_publisher_group(
                self.request,
                self.other_publisher_group.name,
                publisher_group_id=self.other_publisher_group.id,
                account_id=self.other_account.id,
                default_include_subdomains=self.other_publisher_group.default_include_subdomains,
            )

    def test_can_not_create_publisher_group_for_foreign_account(self):
        pg_name = "somerandomname"
        self.assertEqual(models.PublisherGroup.objects.filter(name=pg_name).count(), 0)
        with self.assertRaises(models.Account.DoesNotExist):
            service.get_or_create_publisher_group(
                self.request,
                pg_name,
                publisher_group_id=None,
                account_id=self.other_account.id,
                default_include_subdomains=True,
            )


class GetOrCreatePublisherGroupTestCase(FutureCoreTestCase, LegacyGetOrCreatePublisherGroupTestCase):
    pass


class AddPublisherGroupEntriesTestCase(FutureCoreTestCase):
    def setUp(self):
        self.source = magic_mixer.blend(models.Source)
        self.request = magic_mixer.blend_request_user()
        self.publisher_1 = "example.com"
        self.publisher_2 = "publisher.com"
        self.placement_2 = "00000000-0029-e16a-0000-000000000071"
        self.publisher_group_1 = magic_mixer.blend(models.PublisherGroup)
        self.publisher_group_2 = magic_mixer.blend(models.PublisherGroup)

        self.pge_1 = magic_mixer.blend(
            models.PublisherGroupEntry,
            source=self.source,
            publisher=self.publisher_2,
            placement=self.placement_2,
            includeSubdomains=False,
            publisher_group=self.publisher_group_2,
        )
        self.pge_2 = magic_mixer.blend(
            models.PublisherGroupEntry,
            source=self.source,
            publisher=self.publisher_1,
            includeSubdomains=True,
            publisher_group=self.publisher_group_2,
        )
        self.pge_3 = magic_mixer.blend(
            models.PublisherGroupEntry,
            source=self.source,
            publisher=self.publisher_2,
            includeSubdomains=True,
            publisher_group=self.publisher_group_2,
        )

    def _get_history_entries(self):
        return models.History.objects.filter(
            created_by=self.request.user,
            level=constants.HistoryLevel.GLOBAL,
            action_type=constants.HistoryActionType.GLOBAL_PUBLISHER_BLACKLIST_CHANGE,
        )

    def test_add_publisher_group_entries(self):
        self.assertEqual(self.publisher_group_1.entries.count(), 0)
        self.assertEqual(self._get_history_entries().count(), 0)
        entries = service.add_publisher_group_entries(
            self.request,
            self.publisher_group_1,
            [
                {"source": self.source, "publisher": self.publisher_1, "placement": None, "include_subdomains": True},
                {
                    "source": self.source,
                    "publisher": self.publisher_2,
                    "placement": self.placement_2,
                    "include_subdomains": False,
                },
            ],
        )
        self.assertEqual(len(entries), 2)
        self.assertEqual(self.publisher_group_1.entries.count(), 2)

        history_entries = list(self._get_history_entries())
        self.assertEqual(len(history_entries), 1)
        self.assertTrue("Added the following publishers globally" in history_entries[0].changes_text)

    def test_add_no_entries(self):
        self.assertEqual(self.publisher_group_2.entries.count(), 3)
        self.assertEqual(self._get_history_entries().count(), 0)
        entries = service.add_publisher_group_entries(self.request, self.publisher_group_2, [])
        self.assertEqual(len(entries), 0)
        self.assertEqual(self.publisher_group_2.entries.count(), 3)
        self.assertEqual(self._get_history_entries().count(), 0)

    def test_replace_publisher_group_entries(self):
        self.assertEqual(self.publisher_group_2.entries.count(), 3)
        self.assertEqual(self._get_history_entries().count(), 0)
        entries = service.add_publisher_group_entries(
            self.request,
            self.publisher_group_2,
            [
                {"source": self.source, "publisher": self.publisher_1, "placement": None, "include_subdomains": True},
                {
                    "source": self.source,
                    "publisher": self.publisher_2,
                    "placement": self.placement_2,
                    "include_subdomains": False,
                },
            ],
        )
        self.assertEqual(len(entries), 2)
        self.assertEqual(self.publisher_group_2.entries.count(), 3)

        history_entries = list(self._get_history_entries())
        self.assertEqual(len(history_entries), 1)
        self.assertTrue("Added the following publishers globally" in history_entries[0].changes_text)

        self.assertFalse(self.publisher_group_2.entries.filter(id__in=[self.pge_1.id, self.pge_2.id]).exists())
        self.assertTrue(self.publisher_group_2.entries.filter(id=self.pge_3.id).exists())


class LegacyPublisherGroupConnectionsTestCase(CoreTestCase):
    def setUp(self):
        super().setUp()
        self.request = get_request_mock(self.user)
        self.agency = self.mix_agency(self.request.user, permissions=[Permission.READ, Permission.WRITE])
        self.account = magic_mixer.blend(models.Account, agency=self.agency)
        self.campaign = magic_mixer.blend(models.Campaign, account=self.account)
        self.ad_group = magic_mixer.blend(models.AdGroup, campaign=self.campaign)
        self.publisher_group_1 = magic_mixer.blend(models.PublisherGroup, account=self.account)
        self.publisher_group_2 = magic_mixer.blend(models.PublisherGroup, agency=self.agency)
        self.hidden_agency = magic_mixer.blend(models.Agency)
        self.hidden_account = magic_mixer.blend(models.Account, agency=self.hidden_agency)
        self.hidden_campaign = magic_mixer.blend(models.Campaign, account=self.hidden_account)
        self.hidden_ad_group = magic_mixer.blend(models.AdGroup, campaign=self.hidden_campaign)
        self.hidden_publisher_group_1 = magic_mixer.blend(models.PublisherGroup, account=self.hidden_account)
        self.hidden_publisher_group_2 = magic_mixer.blend(models.PublisherGroup, agency=self.hidden_agency)

    def test_get_connections(self):
        self.agency.settings.update(self.request, whitelist_publisher_groups=[self.publisher_group_2.id])
        self.account.settings.update(self.request, blacklist_publisher_groups=[self.publisher_group_1.id])
        self.campaign.settings.update(self.request, whitelist_publisher_groups=[self.publisher_group_1.id])
        self.ad_group.settings.update(self.request, blacklist_publisher_groups=[self.publisher_group_2.id])

        num_queries = 1
        if self.request.user.has_perm("zemauth.fea_use_entity_permission"):
            # extra 8 query for all entities permission check
            num_queries += 8

        with self.assertNumQueries(num_queries):
            connections = service.get_publisher_group_connections(self.request.user, self.publisher_group_2.id)

        self.assertCountEqual(
            connections,
            [
                {
                    "id": self.agency.id,
                    "name": self.agency.name,
                    "location": connection_definitions.CONNECTION_TYPE_AGENCY_WHITELIST,
                    "user_access": True,
                },
                {
                    "id": self.ad_group.id,
                    "name": self.ad_group.name,
                    "location": connection_definitions.CONNECTION_TYPE_AD_GROUP_BLACKLIST,
                    "user_access": True,
                },
            ],
        )

        with self.assertNumQueries(num_queries):
            connections = service.get_publisher_group_connections(self.request.user, self.publisher_group_1.id)

        self.assertCountEqual(
            connections,
            [
                {
                    "id": self.account.id,
                    "name": self.account.name,
                    "location": connection_definitions.CONNECTION_TYPE_ACCOUNT_BLACKLIST,
                    "user_access": True,
                },
                {
                    "id": self.campaign.id,
                    "name": self.campaign.name,
                    "location": connection_definitions.CONNECTION_TYPE_CAMPAIGN_WHITELIST,
                    "user_access": True,
                },
            ],
        )

    def test_get_hidden_connections_authorized(self):
        self.hidden_agency.settings.update(None, whitelist_publisher_groups=[self.hidden_publisher_group_2.id])
        self.hidden_account.settings.update(None, blacklist_publisher_groups=[self.hidden_publisher_group_1.id])
        self.hidden_campaign.settings.update(None, whitelist_publisher_groups=[self.hidden_publisher_group_1.id])
        self.hidden_ad_group.settings.update(None, blacklist_publisher_groups=[self.hidden_publisher_group_2.id])

        connections = service.get_publisher_group_connections(self.request.user, self.hidden_publisher_group_2.id)

        self.assertCountEqual(connections, [])

        connections = service.get_publisher_group_connections(self.request.user, self.hidden_publisher_group_1.id)

        self.assertCountEqual(connections, [])

    def test_get_hidden_connections_unauthorized(self):
        self.hidden_agency.settings.update(None, whitelist_publisher_groups=[self.hidden_publisher_group_2.id])
        self.hidden_account.settings.update(None, blacklist_publisher_groups=[self.hidden_publisher_group_1.id])
        self.hidden_campaign.settings.update(None, whitelist_publisher_groups=[self.hidden_publisher_group_1.id])
        self.hidden_ad_group.settings.update(None, blacklist_publisher_groups=[self.hidden_publisher_group_2.id])

        connections = service.get_publisher_group_connections(self.request.user, self.hidden_publisher_group_2.id, True)

        self.assertCountEqual(
            connections,
            [
                {
                    "id": self.hidden_agency.id,
                    "name": self.hidden_agency.name,
                    "location": connection_definitions.CONNECTION_TYPE_AGENCY_WHITELIST,
                    "user_access": False,
                },
                {
                    "id": self.hidden_ad_group.id,
                    "name": self.hidden_ad_group.name,
                    "location": connection_definitions.CONNECTION_TYPE_AD_GROUP_BLACKLIST,
                    "user_access": False,
                },
            ],
        )

        connections = service.get_publisher_group_connections(self.request.user, self.hidden_publisher_group_1.id, True)

        self.assertCountEqual(
            connections,
            [
                {
                    "id": self.hidden_account.id,
                    "name": self.hidden_account.name,
                    "location": connection_definitions.CONNECTION_TYPE_ACCOUNT_BLACKLIST,
                    "user_access": False,
                },
                {
                    "id": self.hidden_campaign.id,
                    "name": self.hidden_campaign.name,
                    "location": connection_definitions.CONNECTION_TYPE_CAMPAIGN_WHITELIST,
                    "user_access": False,
                },
            ],
        )

    def test_get_connections_foreign_entities(self):
        foreign_agency = magic_mixer.blend(models.Agency)
        foreign_account = magic_mixer.blend(models.Account, agency=foreign_agency)
        foreign_publisher_group = magic_mixer.blend(models.PublisherGroup, account=foreign_account)
        foreign_agency.settings.update(self.request, whitelist_publisher_groups=[foreign_publisher_group.id])

        num_queries = 1
        if self.request.user.has_perm("zemauth.fea_use_entity_permission"):
            # extra 8 query for all entities permission check
            num_queries += 8

        with self.assertNumQueries(num_queries):
            connections = service.get_publisher_group_connections(self.request.user, foreign_publisher_group.id)

        self.assertCountEqual(connections, [])

    def test_get_connections_foreign_entities_can_see_all_accounts(self):
        test_helper.add_permissions(self.request.user, ["can_see_all_accounts"])

        foreign_agency = magic_mixer.blend(models.Agency)
        foreign_account = magic_mixer.blend(models.Account, agency=foreign_agency)
        foreign_publisher_group = magic_mixer.blend(models.PublisherGroup, account=foreign_account)
        foreign_agency.settings.update(self.request, whitelist_publisher_groups=[foreign_publisher_group.id])

        num_queries = 1
        if self.request.user.has_perm("zemauth.fea_use_entity_permission"):
            # extra 8 query for all entities permission check
            num_queries += 8

        with self.assertNumQueries(num_queries):
            connections = service.get_publisher_group_connections(self.request.user, foreign_publisher_group.id)

        self.assertCountEqual(
            connections,
            [
                {
                    "id": foreign_agency.id,
                    "name": foreign_agency.name,
                    "location": connection_definitions.CONNECTION_TYPE_AGENCY_WHITELIST,
                    "user_access": True,
                }
            ],
        )

    def test_remove_agency_whitelist_connections(self):
        self.agency.settings.update(self.request, whitelist_publisher_groups=[self.publisher_group_2.id])

        self.assertEqual(self.agency.settings.whitelist_publisher_groups, [self.publisher_group_2.id])

        service.remove_publisher_group_connection(
            self.request,
            self.publisher_group_2.id,
            connection_definitions.CONNECTION_TYPE_AGENCY_WHITELIST,
            self.agency.id,
        )

        self.agency.refresh_from_db()
        self.assertEqual(self.agency.settings.whitelist_publisher_groups, [])

    def test_remove_account_blacklist_connections(self):
        self.account.settings.update(self.request, blacklist_publisher_groups=[self.publisher_group_1.id])

        self.assertEqual(self.account.settings.blacklist_publisher_groups, [self.publisher_group_1.id])

        service.remove_publisher_group_connection(
            self.request,
            self.publisher_group_1.id,
            connection_definitions.CONNECTION_TYPE_ACCOUNT_BLACKLIST,
            self.account.id,
        )

        self.account.refresh_from_db()
        self.assertEqual(self.account.settings.blacklist_publisher_groups, [])

    def test_remove_campaign_whitelist_connections(self):
        self.campaign.settings.update(self.request, whitelist_publisher_groups=[self.publisher_group_1.id])

        self.assertEqual(self.campaign.settings.whitelist_publisher_groups, [self.publisher_group_1.id])

        service.remove_publisher_group_connection(
            self.request,
            self.publisher_group_1.id,
            connection_definitions.CONNECTION_TYPE_CAMPAIGN_WHITELIST,
            self.campaign.id,
        )

        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.settings.whitelist_publisher_groups, [])

    def test_remove_ad_group_blacklist_connections(self):
        self.ad_group.settings.update(self.request, blacklist_publisher_groups=[self.publisher_group_2.id])

        self.assertEqual(self.ad_group.settings.blacklist_publisher_groups, [self.publisher_group_2.id])

        service.remove_publisher_group_connection(
            self.request,
            self.publisher_group_2.id,
            connection_definitions.CONNECTION_TYPE_AD_GROUP_BLACKLIST,
            self.ad_group.id,
        )

        self.ad_group.refresh_from_db()
        self.assertEqual(self.ad_group.settings.blacklist_publisher_groups, [])

    def test_remove_connections_invalid_location(self):
        with self.assertRaises(connection_definitions.InvalidConnectionType):
            service.remove_publisher_group_connection(
                self.request, self.publisher_group_2.id, "invalid location", self.ad_group.id
            )

    def test_remove_connections_invalid_connection_id(self):
        with self.assertRaises(models.AdGroup.DoesNotExist):
            service.remove_publisher_group_connection(
                self.request, self.publisher_group_2.id, connection_definitions.CONNECTION_TYPE_AD_GROUP_BLACKLIST, -1
            )

    def test_remove_connections_invalid_publisher_group_id(self):
        with self.assertRaises(ValueError):
            service.remove_publisher_group_connection(
                self.request,
                self.publisher_group_2.id,
                connection_definitions.CONNECTION_TYPE_AD_GROUP_BLACKLIST,
                self.ad_group.id,
            )


class PublisherGroupConnectionsTestCase(FutureCoreTestCase, LegacyPublisherGroupConnectionsTestCase):
    def test_get_connections_foreign_entities_can_see_all_accounts(self):
        self.request.user.entitypermission_set.all().delete()
        magic_mixer.blend(
            zemauth.features.entity_permission.EntityPermission,
            user=self.request.user,
            agency=None,
            account=None,
            permission=Permission.READ,
        )
        magic_mixer.blend(
            zemauth.features.entity_permission.EntityPermission,
            user=self.request.user,
            agency=None,
            account=None,
            permission=Permission.WRITE,
        )
        super().test_get_connections_foreign_entities_can_see_all_accounts()
