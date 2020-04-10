import csv
import io
import textwrap

import mock
from django.http.request import HttpRequest
from django.test import TestCase
from django.test import override_settings

import zemauth.models
from dash import history_helpers
from dash import models
from utils.magic_mixer import magic_mixer

from . import csv_helper
from . import exceptions
from . import service


class PublisherGroupHelpersTest(TestCase):
    fixtures = ["test_publishers.yaml"]

    def setUp(self):
        self.request = HttpRequest()
        self.request.user = zemauth.models.User.objects.get(id=1)

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

    @mock.patch("core.features.publisher_groups.service.ping_k1")
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

    @mock.patch("core.features.publisher_groups.service.ping_k1")
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

    @mock.patch("core.features.publisher_groups.service.ping_k1")
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

    @mock.patch("core.features.publisher_groups.service.ping_k1")
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

    @mock.patch("core.features.publisher_groups.service.ping_k1")
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

    @mock.patch("core.features.publisher_groups.service.ping_k1")
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

    @mock.patch("core.features.publisher_groups.service.ping_k1")
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

    @mock.patch("core.features.publisher_groups.service.ping_k1")
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

    @mock.patch("core.features.publisher_groups.service.ping_k1")
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

    @mock.patch("core.features.publisher_groups.service.ping_k1")
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

    @mock.patch("core.features.publisher_groups.service.ping_k1")
    @mock.patch("utils.email_helper.send_obj_changes_notification_email")
    def test_whitelist_publisher_global(self, mock_email, mock_k1_ping):
        with self.assertRaises(exceptions.PublisherGroupTargetingException):
            # not available
            service.whitelist_publishers(
                self.request, [{"publisher": "cnn.com", "source": None, "include_subdomains": False}], None
            )
            self.assertFalse(mock_email.called)
            mock_k1_ping.assert_not_called()

    @mock.patch("core.features.publisher_groups.service.ping_k1")
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


class PublisherGroupCSVHelpersTest(TestCase):
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
