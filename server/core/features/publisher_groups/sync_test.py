import gzip
import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from unittest import mock

from django.conf import settings
from django.test import TestCase

import core.features.publisher_groups
import core.models
from utils import s3helpers
from utils.magic_mixer import magic_mixer

from . import sync


class SyncBlacklistTest(TestCase):
    utc_now = datetime.utcnow()

    @mock.patch("utils.dates_helper.utc_now", return_value=utc_now)
    @mock.patch.object(s3helpers, "S3Helper")
    @mock.patch.object(sync, "_get_data", autospec=True)
    def test_sync_publisher_groups(self, mock_get_data, s3_helper_mock, mock_utc_now):
        mock_s3_helper = s3helpers.S3Helper()
        s3_helper_mock.return_value = mock_s3_helper
        mock_get_data.return_value = {
            "publisherGroupsLookupTree": {"groups": {"domain": {"plac1": ["id"]}}},
            "subdomainPublisherGroupsLookupTree": {"subdomain_groups": {"domain": {"": ["id"]}}},
            "annotationsLookupTree": {"annotations": {"domain": {"group": "lookup_tree"}}},
            "syncedPublisherGroupIds": [1, 2, 3],
        }
        timestamp = self.utc_now.strftime(sync.FILENAME_SAFE_TIME_FORMAT)
        path = os.path.join(sync.B1_S3_PUBLISHER_GROUPS_PREFIX, timestamp, "full", timestamp + ".gz")
        content = '''annotationsLookupTree:1
publisherGroupsLookupTree:1
subdomainPublisherGroupsLookupTree:1
syncedPublisherGroupIds:3
"annotations","domain","group","""lookup_tree"""
"groups","domain","plac1","[""id""]"
"subdomain_groups","domain","","[""id""]"
"1"
"2"
"3"
'''

        sync.sync_publisher_groups()

        mock_s3_helper.put.assert_has_calls([mock.call(path, gzip.compress(content.encode()))])
        mock_s3_helper.list.assert_has_calls([mock.call(sync.B1_S3_PUBLISHER_GROUPS_PREFIX + "/")])
        mock_s3_helper.delete.assert_has_calls([])

    def test_publisher_groups_lookup_tree(self):
        publisher_group_entries = [
            {
                "account_id": 1,
                "source_slug": "",
                "publisher": "pub1",
                "placement": "",
                "publisher_group_id": 1,
                "outbrain_publisher_id": "12345",
                "include_subdomains": False,
            },
            {
                "account_id": 1,
                "source_slug": "adblade",
                "publisher": "pub1",
                "placement": "plac1",
                "publisher_group_id": 2,
                "outbrain_publisher_id": "12345",
                "include_subdomains": False,
            },
            {
                "account_id": 1,
                "source_slug": "gumgum",
                "publisher": "pub1",
                "placement": None,
                "publisher_group_id": 3,
                "outbrain_publisher_id": "12345",
                "include_subdomains": True,
            },
            {
                "account_id": 1,
                "source_slug": "gumgum",
                "publisher": "pub1",
                "publisher_group_id": 4,
                "outbrain_publisher_id": "12345",
                "include_subdomains": True,
            },
            {
                "account_id": 1,
                "source_slug": "",
                "publisher": "pub2",
                "placement": "plac3",
                "publisher_group_id": 5,
                "outbrain_publisher_id": "12345",
                "include_subdomains": True,
            },
        ]
        groups_lookup_tree = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        subdomain_groups_lookup_tree = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        expected_groups_lookup_tree = {
            "": {"pub1": {"": ["1"]}, "pub2": {"plac3": ["5"]}},
            "adblade": {"pub1": {"plac1": ["2"]}},
            "gumgum": {"pub1": {"": ["3", "4"]}},
        }
        expected_subdomain_groups_lookup_tree = {"": {"pub2": {"plac3": ["5"]}}, "gumgum": {"pub1": {"": ["3", "4"]}}}

        for entry in publisher_group_entries:
            sync._insert_into_lookup_trees(entry, groups_lookup_tree, subdomain_groups_lookup_tree)

        self.assertEqual(expected_groups_lookup_tree, groups_lookup_tree)
        self.assertEqual(expected_subdomain_groups_lookup_tree, subdomain_groups_lookup_tree)

    def test_annotations_lookup_tree(self):
        sync.ANNOTATION_QUALIFIED_PUBLISHER_GROUPS = set([1, 2, 3, 4])

        publisher_group_entries = [
            {
                "account_id": 1,
                "source_slug": None,
                "publisher": "pub1",
                "publisher_group_id": 1,
                "outbrain_publisher_id": "12345",
                "outbrain_section_id": "100",
                "outbrain_amplify_publisher_id": "200",
                "outbrain_engage_publisher_id": "300",
            },
            {
                "account_id": 1,
                "source_slug": "adblade",
                "publisher": "pub1",
                "publisher_group_id": 2,
                "outbrain_publisher_id": "12346",
                "outbrain_section_id": "101",
                "outbrain_amplify_publisher_id": "201",
                "outbrain_engage_publisher_id": "202",
            },
            {
                "account_id": 1,
                "source_slug": "gumgum",
                "publisher": "pub1",
                "publisher_group_id": 3,
                "outbrain_publisher_id": "12347",
            },
            {
                "account_id": 1,
                "source_slug": "gumgum",
                "publisher": "pub1",
                "publisher_group_id": 4,
                "outbrain_publisher_id": "12348",
                "outbrain_section_id": "103",
                "outbrain_amplify_publisher_id": "203",
                "outbrain_engage_publisher_id": "204",
            },
            {
                "account_id": 1,
                "source_slug": "gumgum",
                "publisher": "pub2",
                "publisher_group_id": 4,
                "outbrain_publisher_id": None,
            },
        ]
        expected = sync.tree()
        expected[1]["pub1"][""] = {
            "outbrainPublisherID": "12345",
            "outbrainSectionID": "100",
            "outbrainAmplifyPublisherID": "200",
            "outbrainEngagePublisherID": "300",
        }
        expected[1]["pub1"]["adblade"] = {
            "outbrainPublisherID": "12346",
            "outbrainSectionID": "101",
            "outbrainAmplifyPublisherID": "201",
            "outbrainEngagePublisherID": "202",
        }
        expected[1]["pub1"]["gumgum"] = {
            "outbrainPublisherID": "12348",
            "outbrainSectionID": "103",
            "outbrainAmplifyPublisherID": "203",
            "outbrainEngagePublisherID": "204",
        }

        annotations_lookup_tree = sync.tree()
        for entry in publisher_group_entries:
            sync._insert_into_annotations_lookup_tree(entry, annotations_lookup_tree)

        self.assertEqual(expected, annotations_lookup_tree)

    def test_sanitize_names(self):
        entries = [{"publisher": " Pub1", "publisher_group_id": 1}, {"publisher": "Abc.com ", "publisher_group_id": 2}]
        entries_expected = [
            {"publisher": "pub1", "publisher_group_id": 1},
            {"publisher": "abc.com", "publisher_group_id": 2},
        ]
        for entry in entries:
            sync._sanitize_names(entry)
        self.assertEqual(entries, entries_expected)

    def test_marshal(self):
        data = {
            "publisherGroupsLookupTree": {
                "": {"guiadelocio.com": {"plac1": ["233506", "234798"]}},
                "yieldmo": {"m.guiadelocio.com": {"": ["233507"], "plac2": ["234799"]}},
            },
            "subdomainPublisherGroupsLookupTree": {
                "": {"guiadelocio.com": {"": ["213287", "233508"]}},
                "yieldmo": {"m.guiadelocio.com": {"plac1": ["779663"]}},
            },
            "annotationsLookupTree": {
                "305": {
                    "shoryuken.com": {
                        "adsnative": {
                            "outbrainSectionID": "6685490",
                            "outbrainAmplifyPublisherID": "30956",
                            "outbrainEngagePublisherID": "11536",
                        }
                    }
                }
            },
            "syncedPublisherGroupIds": ["330229", "330230"],
        }

        expected_content = """annotationsLookupTree:1
publisherGroupsLookupTree:3
subdomainPublisherGroupsLookupTree:2
syncedPublisherGroupIds:2
"305","shoryuken.com","adsnative","{""outbrainSectionID"": ""6685490"", ""outbrainAmplifyPublisherID"": ""30956"", ""outbrainEngagePublisherID"": ""11536""}"
"","guiadelocio.com","plac1","[""233506"", ""234798""]"
"yieldmo","m.guiadelocio.com","","[""233507""]"
"yieldmo","m.guiadelocio.com","plac2","[""234799""]"
"","guiadelocio.com","","[""213287"", ""233508""]"
"yieldmo","m.guiadelocio.com","plac1","[""779663""]"
"330229"
"330230"
"""

        # we can't compare whole file because order is not necessary the same
        content = sync._marshal(data)
        self.assertEqual(content, expected_content)

    @mock.patch("utils.dates_helper.utc_now", return_value=utc_now)
    @mock.patch.object(s3helpers, "S3Helper")
    def test_remove_old_publisher_groups_update(self, s3_helper_mock, mock_utc_now):
        @dataclass
        class MockS3Key(object):
            name: str

        mock_s3_helper = s3helpers.S3Helper()
        s3_helper_mock.return_value = mock_s3_helper
        mock_s3_helper.list.return_value = [MockS3Key(str(i)) for i in range(sync.KEEP_LAST_UPDATES * 2)]

        sync._remove_old_publisher_groups_files(mock_s3_helper)

        mock_s3_helper.list.assert_has_calls([mock.call(sync.B1_S3_PUBLISHER_GROUPS_PREFIX + "/")])
        mock_s3_helper.delete.assert_has_calls([mock.call(str(i)) for i in reversed(range(sync.KEEP_LAST_UPDATES - 1))])


@mock.patch("django.conf.settings.SOURCE_GROUPS", {settings.HARDCODED_SOURCE_ID_OUTBRAINRTB: [81]})
class SyncBlacklistSourceGroupsTest(TestCase):
    def setUp(self):
        self.parent_source = magic_mixer.blend(core.models.Source, id=settings.HARDCODED_SOURCE_ID_OUTBRAINRTB)
        self.grouped_source = magic_mixer.blend(core.models.Source, id=81)

        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account__agency__uses_source_groups=True)

        self.publisher_group = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroup, account=self.ad_group.campaign.account
        )
        self.publisher_group_entry = magic_mixer.blend(
            core.features.publisher_groups.PublisherGroupEntry,
            publisher_group=self.publisher_group,
            source=self.parent_source,
        )
        # deprecated publisher group entry
        magic_mixer.blend(
            core.features.publisher_groups.PublisherGroupEntry,
            publisher_group=self.publisher_group,
            source=self.grouped_source,
        )

        self.ad_group.settings.update_unsafe(None, blacklist_publisher_groups=[self.publisher_group.id])

    def test_sync_publisher_groups_source_groups(self):
        data = sync._get_data()

        self.assertCountEqual(
            {
                "publisherGroupsLookupTree": {
                    self.grouped_source.bidder_slug: {
                        self.publisher_group_entry.publisher: {
                            self.publisher_group_entry.placement: [str(self.publisher_group.id)]
                        }
                    },
                    self.parent_source.bidder_slug: {
                        self.publisher_group_entry.publisher: {
                            self.publisher_group_entry.placement: [str(self.publisher_group.id)]
                        }
                    },
                },
                "subdomainPublisherGroupsLookupTree": {
                    self.grouped_source.bidder_slug: {
                        self.publisher_group_entry.publisher: {
                            self.publisher_group_entry.placement: [str(self.publisher_group)]
                        }
                    },
                    self.parent_source.bidder_slug: {
                        self.publisher_group_entry.publisher: {
                            self.publisher_group_entry.placement: [str(self.publisher_group.id)]
                        }
                    },
                },
                "annotationsLookupTree": {},
                "syncedPublisherGroupIds": [self.publisher_group],
            },
            data,
        )

    def test_sync_publisher_groups_source_groups_oen(self):
        account = magic_mixer.blend(
            core.models.Account, id=settings.HARDCODED_ACCOUNT_ID_OEN, agency__uses_source_groups=True
        )
        self.ad_group.campaign.account = account

        data = sync._get_data()

        self.assertCountEqual(
            {
                "publisherGroupsLookupTree": {
                    self.grouped_source.bidder_slug: {
                        self.publisher_group_entry.publisher: {
                            self.publisher_group_entry.placement: [str(self.publisher_group.id)]
                        }
                    }
                },
                "subdomainPublisherGroupsLookupTree": {
                    self.grouped_source.bidder_slug: {
                        self.publisher_group_entry.publisher: {
                            self.publisher_group_entry.placement: [str(self.publisher_group)]
                        }
                    }
                },
                "annotationsLookupTree": {},
                "syncedPublisherGroupIds": [self.publisher_group],
            },
            data,
        )
