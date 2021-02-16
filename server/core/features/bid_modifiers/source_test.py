import decimal
from datetime import timedelta

import mock
from django.test import TestCase

import utils.exc
from core.features import bid_modifiers
from core.features.multicurrency.service.update import _recalculate_ad_group_amounts
from core.models.settings.ad_group_settings import exceptions as ag_exceptions
from core.models.settings.ad_group_source_settings import exceptions as ags_exceptions
from dash import constants
from dash import models
from utils import dates_helper
from utils import decimal_helpers
from utils.magic_mixer import magic_mixer


class SourceBidValidationMixin(object):
    def setUp(self):
        self.request = magic_mixer.blend_request_user()
        self.ad_group = magic_mixer.blend(models.AdGroup)
        self.ad_group.settings.update_unsafe(
            None, b1_sources_group_enabled=False, autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE
        )
        self.input_bid_modifiers_list = [0.3, 1.4]

    def _add_sources_with_modifiers(self, modifiers_list, bid_value=None):

        if self.ad_group.bidding_type == constants.BiddingType.CPC:
            bid_value_attr = "cpc"
            source_bid_value_attr = "cpc_cc"
        else:
            bid_value_attr = "cpm"
            source_bid_value_attr = "cpm"

        if bid_value is None:
            bid_value = decimal.Decimal(getattr(self.ad_group.settings, bid_value_attr))

        for modifier in modifiers_list:
            ad_group_source = magic_mixer.blend(models.AdGroupSource, ad_group=self.ad_group)
            magic_mixer.blend(
                models.BidModifier,
                ad_group=self.ad_group,
                type=bid_modifiers.BidModifierType.SOURCE,
                modifier=modifier,
                target=bid_modifiers.TargetConverter._to_source_target(
                    ad_group_source.source.bidder_slug, bid_modifiers.BidModifierType.SOURCE
                ),
            )
            ad_group_source.settings.update(None, **{source_bid_value_attr: decimal.Decimal(modifier) * bid_value})

    def _get_source_bid_modifier(self, ad_group_source):
        return models.BidModifier.objects.get(
            ad_group=self.ad_group,
            type=bid_modifiers.BidModifierType.SOURCE,
            target=bid_modifiers.TargetConverter._to_source_target(
                ad_group_source.source.bidder_slug, bid_modifiers.BidModifierType.SOURCE
            ),
        )

    def _assert_bid_modifiers(self, expected_bid_modifiers_list):
        output_bid_modifiers_list = list(
            self.ad_group.bidmodifier_set.filter(type=bid_modifiers.BidModifierType.SOURCE)
            .order_by("id")
            .values_list("modifier", flat=True)
        )
        self.assertEqual(output_bid_modifiers_list, expected_bid_modifiers_list)

    def _assert_ad_group_bid_values(self, cpc=None, cpm=None):
        if cpc is not None:
            self.assertEqual(self.ad_group.settings.cpc, cpc)
        if cpm is not None:
            self.assertEqual(self.ad_group.settings.cpm, cpm)

    def _assert_write_history_calls(self, entries, mock_calls):
        self.assertEqual(len(entries), len(mock_calls), msg=str(mock_calls))
        # since the order of source history records can vary a more complex algorithm is needed
        found = set()
        for mock_call in mock_calls:
            self.assertEqual(len(mock_call[0]), 1)
            for i, entry in enumerate(entries):
                if i in found:
                    continue

                match = True
                for s in entry[0]:
                    if s not in mock_call[0][0]:
                        match = False
                        break

                if match:
                    found.add(i)
                    self.assertEqual(entry[1], mock_call[1])
                    break

        self.assertEqual(len(found), len(mock_calls), msg=str(mock_calls))


class AdGroupSettingsChangeTestCase(SourceBidValidationMixin, TestCase):
    def test_cpc(self):
        self.ad_group.settings.update_unsafe(
            None,
            state=constants.AdGroupSettingsState.ACTIVE,
            cpc=decimal.Decimal("0.1"),
            local_cpc=decimal.Decimal("0.1"),
            cpm=decimal.Decimal("1.0"),
            local_cpm=decimal.Decimal("1.0"),
        )

        self._add_sources_with_modifiers(self.input_bid_modifiers_list)

        send_task_patcher = mock.patch("utils.k1_helper._send_task")
        write_history_patcher = mock.patch.object(models.AdGroup, "write_history")

        mock_send_task = send_task_patcher.start()
        mock_write_history = write_history_patcher.start()

        self.ad_group.settings.update(self.request, cpc=decimal.Decimal("0.2"))

        send_task_patcher.stop()
        write_history_patcher.stop()

        self._assert_ad_group_bid_values(cpc=decimal.Decimal("0.2"), cpm=decimal.Decimal("1.0"))
        self._assert_bid_modifiers(self.input_bid_modifiers_list)

        self.assertEqual(mock_send_task.call_count, 1)
        mock_send_task.assert_has_calls(
            [
                mock.call(
                    "k1-consistency_ping_ad_group",
                    "consistency_ping_ad_group",
                    account_id=self.ad_group.campaign.account.id,
                    ad_group_id=self.ad_group.id,
                    msg="AdGroupSettings.put",
                    priority=True,
                )
            ]
        )
        self._assert_write_history_calls(
            [
                [
                    ["Created settings", 'Bid CPC set from "$0.100" to "$0.200"'],
                    {
                        "action_type": constants.HistoryActionType.SETTINGS_CHANGE,
                        "changes": {"local_cpc": decimal.Decimal("0.2000")},
                        "system_user": None,
                        "user": self.request.user,
                    },
                ],
            ],
            mock_write_history.call_args_list,
        )

    def test_cpm(self):
        self.ad_group.settings.update_unsafe(
            None,
            state=constants.AdGroupSettingsState.ACTIVE,
            cpc=decimal.Decimal("0.1"),
            local_cpc=decimal.Decimal("0.1"),
            cpm=decimal.Decimal("1.0"),
            local_cpm=decimal.Decimal("1.0"),
        )
        self.ad_group.bidding_type = constants.BiddingType.CPM
        self.ad_group.save(None)

        self._add_sources_with_modifiers(self.input_bid_modifiers_list)

        send_task_patcher = mock.patch("utils.k1_helper._send_task")
        write_history_patcher = mock.patch.object(models.AdGroup, "write_history")

        mock_send_task = send_task_patcher.start()
        mock_write_history = write_history_patcher.start()

        self.ad_group.settings.update(self.request, cpm=decimal.Decimal("2.0"))

        send_task_patcher.stop()
        write_history_patcher.stop()

        self._assert_ad_group_bid_values(cpc=decimal.Decimal("0.1"), cpm=decimal.Decimal("2.0"))
        self._assert_bid_modifiers(self.input_bid_modifiers_list)

        self.assertEqual(mock_send_task.call_count, 1)
        mock_send_task.assert_has_calls(
            [
                mock.call(
                    "k1-consistency_ping_ad_group",
                    "consistency_ping_ad_group",
                    account_id=self.ad_group.campaign.account.id,
                    ad_group_id=self.ad_group.id,
                    msg="AdGroupSettings.put",
                    priority=True,
                )
            ]
        )
        self._assert_write_history_calls(
            [
                [
                    ["Created settings", 'Bid CPM set from "$1.000" to "$2.000"'],
                    {
                        "action_type": constants.HistoryActionType.SETTINGS_CHANGE,
                        "changes": {"local_cpm": decimal.Decimal("2.0000")},
                        "system_user": None,
                        "user": self.request.user,
                    },
                ],
            ],
            mock_write_history.call_args_list,
        )


class AdGroupSourceSettingsChangeTestCase(SourceBidValidationMixin, TestCase):
    def test_cpc(self):
        self.ad_group.settings.update_unsafe(None, cpc=decimal.Decimal("0.1"), cpm=decimal.Decimal("1.0"))

        self._add_sources_with_modifiers(self.input_bid_modifiers_list)

        send_task_patcher = mock.patch("utils.k1_helper._send_task")
        write_history_patcher = mock.patch.object(models.AdGroup, "write_history")

        mock_send_task = send_task_patcher.start()
        mock_write_history = write_history_patcher.start()

        ad_group_sources = list(self.ad_group.adgroupsource_set.order_by("id"))
        ad_group_sources[0].settings.update(self.request, cpc_cc=decimal.Decimal("0.06"))
        ad_group_sources[1].settings.update(self.request, cpc_cc=decimal.Decimal("0.3"))

        send_task_patcher.stop()
        write_history_patcher.stop()

        self._assert_ad_group_bid_values(cpc=decimal.Decimal("0.1"), cpm=decimal.Decimal("1.0"))
        self._assert_bid_modifiers([0.6, 3.0])

        self.assertEqual(mock_send_task.call_count, 2)
        mock_send_task.assert_has_calls(
            [
                mock.call(
                    "k1-consistency_ping_ad_group",
                    "consistency_ping_ad_group",
                    account_id=self.ad_group.campaign.account.id,
                    ad_group_id=self.ad_group.id,
                    msg="AdGroupSource.update",
                    priority=False,
                ),
                mock.call(
                    "k1-consistency_ping_ad_group",
                    "consistency_ping_ad_group",
                    account_id=self.ad_group.campaign.account.id,
                    ad_group_id=self.ad_group.id,
                    msg="AdGroupSource.update",
                    priority=False,
                ),
            ]
        )
        self._assert_write_history_calls(
            [
                [
                    ["Source", 'CPC set from "$0.030" to "$0.060"'],
                    {
                        "action_type": constants.HistoryActionType.SETTINGS_CHANGE,
                        "changes": {"local_cpc_cc": decimal.Decimal("0.0600")},
                        "system_user": None,
                        "user": self.request.user,
                    },
                ],
                [
                    ["Bid modifier Source", "set to -40.00%"],
                    {"action_type": constants.HistoryActionType.BID_MODIFIER_UPDATE, "user": self.request.user},
                ],
                [
                    ["Source", 'CPC set from "$0.140" to "$0.300"'],
                    {
                        "action_type": constants.HistoryActionType.SETTINGS_CHANGE,
                        "changes": {"local_cpc_cc": decimal.Decimal("0.3000")},
                        "system_user": None,
                        "user": self.request.user,
                    },
                ],
                [
                    ["Bid modifier Source", "set to 200.00%"],
                    {"action_type": constants.HistoryActionType.BID_MODIFIER_UPDATE, "user": self.request.user},
                ],
            ],
            mock_write_history.call_args_list,
        )

    def test_cpm(self):
        self.ad_group.settings.update_unsafe(None, cpc=decimal.Decimal("0.1"), cpm=decimal.Decimal("1.0"))
        self.ad_group.bidding_type = constants.BiddingType.CPM
        self.ad_group.save(None)

        self._add_sources_with_modifiers(self.input_bid_modifiers_list)

        send_task_patcher = mock.patch("utils.k1_helper._send_task")
        write_history_patcher = mock.patch.object(models.AdGroup, "write_history")

        mock_send_task = send_task_patcher.start()
        mock_write_history = write_history_patcher.start()

        ad_group_sources = list(self.ad_group.adgroupsource_set.order_by("id"))
        ad_group_sources[0].settings.update(self.request, cpm=decimal.Decimal("0.6"))
        ad_group_sources[1].settings.update(self.request, cpm=decimal.Decimal("3.0"))

        send_task_patcher.stop()
        write_history_patcher.stop()

        self._assert_ad_group_bid_values(cpc=decimal.Decimal("0.1"), cpm=decimal.Decimal("1.0"))
        self._assert_bid_modifiers([0.6, 3.0])

        self.assertEqual(mock_send_task.call_count, 2)
        mock_send_task.assert_has_calls(
            [
                mock.call(
                    "k1-consistency_ping_ad_group",
                    "consistency_ping_ad_group",
                    account_id=self.ad_group.campaign.account.id,
                    ad_group_id=self.ad_group.id,
                    msg="AdGroupSource.update",
                    priority=False,
                ),
                mock.call(
                    "k1-consistency_ping_ad_group",
                    "consistency_ping_ad_group",
                    account_id=self.ad_group.campaign.account.id,
                    ad_group_id=self.ad_group.id,
                    msg="AdGroupSource.update",
                    priority=False,
                ),
            ]
        )
        self._assert_write_history_calls(
            [
                [
                    ["Source", 'CPM set from "$0.300" to "$0.600"'],
                    {
                        "action_type": constants.HistoryActionType.SETTINGS_CHANGE,
                        "changes": {"local_cpm": decimal.Decimal("0.6000")},
                        "system_user": None,
                        "user": self.request.user,
                    },
                ],
                [
                    ["Bid modifier Source", "set to -40.00%"],
                    {"action_type": constants.HistoryActionType.BID_MODIFIER_UPDATE, "user": self.request.user},
                ],
                [
                    ["Source", 'CPM set from "$1.400" to "$3.000"'],
                    {
                        "action_type": constants.HistoryActionType.SETTINGS_CHANGE,
                        "changes": {"local_cpm": decimal.Decimal("3.0000")},
                        "system_user": None,
                        "user": self.request.user,
                    },
                ],
                [
                    ["Bid modifier Source", "set to 200.00%"],
                    {"action_type": constants.HistoryActionType.BID_MODIFIER_UPDATE, "user": self.request.user},
                ],
            ],
            mock_write_history.call_args_list,
        )


class SourceBidModifierChangeTestCase(SourceBidValidationMixin, TestCase):
    def test_cpc(self):
        self.ad_group.settings.update_unsafe(None, cpc=decimal.Decimal("0.1"), cpm=decimal.Decimal("1.0"))

        self._add_sources_with_modifiers(self.input_bid_modifiers_list)

        send_task_patcher = mock.patch("utils.k1_helper._send_task")
        write_history_patcher = mock.patch.object(models.AdGroup, "write_history")

        mock_send_task = send_task_patcher.start()
        mock_write_history = write_history_patcher.start()

        ad_group_sources = list(self.ad_group.adgroupsource_set.order_by("id"))

        bm = self._get_source_bid_modifier(ad_group_sources[0])
        bid_modifiers.service.set(bm.ad_group, bm.type, bm.target, bm.source, 0.6, user=self.request.user)
        bm = self._get_source_bid_modifier(ad_group_sources[1])
        bid_modifiers.service.set(bm.ad_group, bm.type, bm.target, bm.source, 3.0, user=self.request.user)

        send_task_patcher.stop()
        write_history_patcher.stop()

        self._assert_ad_group_bid_values(cpc=decimal.Decimal("0.1"), cpm=decimal.Decimal("1.0"))
        self._assert_bid_modifiers([0.6, 3.0])

        self.assertEqual(mock_send_task.call_count, 2)
        mock_send_task.assert_has_calls(
            [
                mock.call(
                    "k1-consistency_ping_ad_group",
                    "consistency_ping_ad_group",
                    account_id=self.ad_group.campaign.account.id,
                    ad_group_id=self.ad_group.id,
                    msg="bid_modifiers.set",
                    priority=True,
                ),
                mock.call(
                    "k1-consistency_ping_ad_group",
                    "consistency_ping_ad_group",
                    account_id=self.ad_group.campaign.account.id,
                    ad_group_id=self.ad_group.id,
                    msg="bid_modifiers.set",
                    priority=True,
                ),
            ]
        )
        self._assert_write_history_calls(
            [
                [
                    ["Bid modifier", "set to -40.00%"],
                    {"action_type": constants.HistoryActionType.BID_MODIFIER_UPDATE, "user": self.request.user},
                ],
                [
                    ["Source", 'CPC set from "$0.030" to "$0.060"'],
                    {
                        "action_type": constants.HistoryActionType.SETTINGS_CHANGE,
                        "changes": {"local_cpc_cc": decimal.Decimal("0.0600")},
                        "system_user": None,
                        "user": None,
                    },
                ],
                [
                    ["Bid modifier", "set to 200.00%"],
                    {"action_type": constants.HistoryActionType.BID_MODIFIER_UPDATE, "user": self.request.user},
                ],
                [
                    ["Source", 'CPC set from "$0.140" to "$0.300"'],
                    {
                        "action_type": constants.HistoryActionType.SETTINGS_CHANGE,
                        "changes": {"local_cpc_cc": decimal.Decimal("0.3000")},
                        "system_user": None,
                        "user": None,
                    },
                ],
            ],
            mock_write_history.call_args_list,
        )

    def test_cpm(self):
        self.ad_group.settings.update_unsafe(None, cpc=decimal.Decimal("0.1"), cpm=decimal.Decimal("1.0"))
        self.ad_group.bidding_type = constants.BiddingType.CPM
        self.ad_group.save(None)

        self._add_sources_with_modifiers(self.input_bid_modifiers_list)

        send_task_patcher = mock.patch("utils.k1_helper._send_task")
        write_history_patcher = mock.patch.object(models.AdGroup, "write_history")

        mock_send_task = send_task_patcher.start()
        mock_write_history = write_history_patcher.start()

        ad_group_sources = list(self.ad_group.adgroupsource_set.order_by("id"))

        bm = self._get_source_bid_modifier(ad_group_sources[0])
        bid_modifiers.service.set(bm.ad_group, bm.type, bm.target, bm.source, 0.6, user=self.request.user)
        bm = self._get_source_bid_modifier(ad_group_sources[1])
        bid_modifiers.service.set(bm.ad_group, bm.type, bm.target, bm.source, 3.0, user=self.request.user)

        send_task_patcher.stop()
        write_history_patcher.stop()

        self._assert_ad_group_bid_values(cpc=decimal.Decimal("0.1"), cpm=decimal.Decimal("1.0"))
        self._assert_bid_modifiers([0.6, 3.0])

        self.assertEqual(mock_send_task.call_count, 2)
        mock_send_task.assert_has_calls(
            [
                mock.call(
                    "k1-consistency_ping_ad_group",
                    "consistency_ping_ad_group",
                    account_id=self.ad_group.campaign.account.id,
                    ad_group_id=self.ad_group.id,
                    msg="bid_modifiers.set",
                    priority=True,
                ),
                mock.call(
                    "k1-consistency_ping_ad_group",
                    "consistency_ping_ad_group",
                    account_id=self.ad_group.campaign.account.id,
                    ad_group_id=self.ad_group.id,
                    msg="bid_modifiers.set",
                    priority=True,
                ),
            ]
        )
        self._assert_write_history_calls(
            [
                [
                    ["Bid modifier", "set to -40.00%"],
                    {"action_type": constants.HistoryActionType.BID_MODIFIER_UPDATE, "user": self.request.user},
                ],
                [
                    ["Source", 'CPM set from "$0.300" to "$0.600"'],
                    {
                        "action_type": constants.HistoryActionType.SETTINGS_CHANGE,
                        "changes": {"local_cpm": decimal.Decimal("0.6000")},
                        "system_user": None,
                        "user": None,
                    },
                ],
                [
                    ["Bid modifier", "set to 200.00%"],
                    {"action_type": constants.HistoryActionType.BID_MODIFIER_UPDATE, "user": self.request.user},
                ],
                [
                    ["Source", 'CPM set from "$1.400" to "$3.000"'],
                    {
                        "action_type": constants.HistoryActionType.SETTINGS_CHANGE,
                        "changes": {"local_cpm": decimal.Decimal("3.0000")},
                        "system_user": None,
                        "user": None,
                    },
                ],
            ],
            mock_write_history.call_args_list,
        )


class SwitchBiddingTypeTestCase(SourceBidValidationMixin, TestCase):
    def _add_sources_with_modifiers(self, modifiers_list, factor=2):
        cpc = decimal.Decimal(self.ad_group.settings.cpc)
        cpm = decimal.Decimal(self.ad_group.settings.cpm)

        for modifier in modifiers_list:
            if self.ad_group.bidding_type == constants.BiddingType.CPC:
                source_cpc = decimal_helpers.multiply_as_decimals(cpc, modifier)
                source_cpm = decimal_helpers.multiply_as_decimals(cpm, modifier * factor)
            else:
                source_cpc = decimal_helpers.multiply_as_decimals(cpc, modifier * factor)
                source_cpm = decimal_helpers.multiply_as_decimals(cpm, modifier)

            ad_group_source = magic_mixer.blend(models.AdGroupSource, ad_group=self.ad_group)
            magic_mixer.blend(
                models.BidModifier,
                ad_group=self.ad_group,
                type=bid_modifiers.BidModifierType.SOURCE,
                modifier=modifier,
                target=bid_modifiers.TargetConverter._to_source_target(
                    ad_group_source.source.bidder_slug, bid_modifiers.BidModifierType.SOURCE
                ),
            )
            ad_group_source.settings.update_unsafe(None, cpc_cc=source_cpc, cpm=source_cpm)

    def test_cpc_to_cpm(self):
        self.ad_group.settings.update_unsafe(None, cpc=decimal.Decimal("0.1"), cpm=decimal.Decimal("1.0"))

        self._add_sources_with_modifiers(self.input_bid_modifiers_list)

        send_task_patcher = mock.patch("utils.k1_helper._send_task")
        write_history_patcher = mock.patch.object(models.AdGroup, "write_history")

        mock_send_task = send_task_patcher.start()
        mock_write_history = write_history_patcher.start()

        self.ad_group.update(self.request, bidding_type=constants.BiddingType.CPM)

        send_task_patcher.stop()
        write_history_patcher.stop()

        self._assert_ad_group_bid_values(cpc=decimal.Decimal("0.1"), cpm=decimal.Decimal("1.0"))
        self._assert_bid_modifiers(self.input_bid_modifiers_list)

        self.assertEqual(mock_send_task.call_count, 1)
        mock_send_task.assert_has_calls(
            [
                mock.call(
                    "k1-consistency_ping_ad_group",
                    "consistency_ping_ad_group",
                    account_id=self.ad_group.campaign.account.id,
                    ad_group_id=self.ad_group.id,
                    msg="Adgroup.update",
                    priority=False,
                )
            ]
        )
        self._assert_write_history_calls(
            [
                [
                    ["Source", 'CPM set to "$1.400"'],
                    {
                        "action_type": constants.HistoryActionType.SETTINGS_CHANGE,
                        "changes": {"local_cpm": decimal.Decimal("1.4000")},
                        "system_user": None,
                        "user": None,
                    },
                ],
                [
                    ["Source", 'CPM set to "$0.300"'],
                    {
                        "action_type": constants.HistoryActionType.SETTINGS_CHANGE,
                        "changes": {"local_cpm": decimal.Decimal("0.3000")},
                        "system_user": None,
                        "user": None,
                    },
                ],
            ],
            mock_write_history.call_args_list,
        )

    def test_cpm_to_cpc(self):
        self.ad_group.settings.update_unsafe(None, cpc=decimal.Decimal("0.1"), cpm=decimal.Decimal("1.0"))
        self.ad_group.bidding_type = constants.BiddingType.CPM
        self.ad_group.save(None)

        self._add_sources_with_modifiers(self.input_bid_modifiers_list)

        send_task_patcher = mock.patch("utils.k1_helper._send_task")
        write_history_patcher = mock.patch.object(models.AdGroup, "write_history")

        mock_send_task = send_task_patcher.start()
        mock_write_history = write_history_patcher.start()

        self.ad_group.update(self.request, bidding_type=constants.BiddingType.CPC)

        send_task_patcher.stop()
        write_history_patcher.stop()

        self._assert_ad_group_bid_values(cpc=decimal.Decimal("0.1"), cpm=decimal.Decimal("1.0"))
        self._assert_bid_modifiers(self.input_bid_modifiers_list)

        self.assertEqual(mock_send_task.call_count, 1)
        mock_send_task.assert_has_calls(
            [
                mock.call(
                    "k1-consistency_ping_ad_group",
                    "consistency_ping_ad_group",
                    account_id=self.ad_group.campaign.account.id,
                    ad_group_id=self.ad_group.id,
                    msg="Adgroup.update",
                    priority=False,
                )
            ]
        )
        self._assert_write_history_calls(
            [
                [
                    ["Source", 'CPC set to "$0.140"'],
                    {
                        "action_type": constants.HistoryActionType.SETTINGS_CHANGE,
                        "changes": {"local_cpc_cc": decimal.Decimal("0.1400")},
                        "system_user": None,
                        "user": None,
                    },
                ],
                [
                    ["Source", 'CPC set to "$0.030"'],
                    {
                        "action_type": constants.HistoryActionType.SETTINGS_CHANGE,
                        "changes": {"local_cpc_cc": decimal.Decimal("0.0300")},
                        "system_user": None,
                        "user": None,
                    },
                ],
            ],
            mock_write_history.call_args_list,
        )


class ValidationTestCase(TestCase):
    def setUp(self):
        self.source_type_1 = magic_mixer.blend(
            models.SourceType,
            min_cpc=decimal.Decimal("0.1"),
            max_cpc=decimal.Decimal("10.0"),
            min_cpm=decimal.Decimal("0.05"),
            max_cpm=decimal.Decimal("5.0"),
        )
        self.source_type_2 = magic_mixer.blend(
            models.SourceType,
            min_cpc=decimal.Decimal("0.005"),
            max_cpc=decimal.Decimal("15.0"),
            min_cpm=decimal.Decimal("0.005"),
            max_cpm=decimal.Decimal("15.0"),
        )
        self.source_1 = magic_mixer.blend(models.Source, source_type=self.source_type_1)
        self.source_2 = magic_mixer.blend(models.Source, source_type=self.source_type_2)

        self.ad_group_1 = magic_mixer.blend(models.AdGroup)
        self.ad_group_1.settings.update_unsafe(
            None, b1_sources_group_enabled=False, autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE
        )

        self.ad_group_source_1_1 = magic_mixer.blend(
            models.AdGroupSource, ad_group=self.ad_group_1, source=self.source_1
        )
        self.ad_group_source_1_2 = magic_mixer.blend(
            models.AdGroupSource, ad_group=self.ad_group_1, source=self.source_2
        )

        self.bm_1_1 = magic_mixer.blend(
            models.BidModifier,
            ad_group=self.ad_group_1,
            type=bid_modifiers.BidModifierType.SOURCE,
            modifier=1.0,
            target=bid_modifiers.TargetConverter._to_source_target(
                self.source_1.bidder_slug, bid_modifiers.BidModifierType.SOURCE
            ),
        )

        self.bm_1_2 = magic_mixer.blend(
            models.BidModifier,
            ad_group=self.ad_group_1,
            type=bid_modifiers.BidModifierType.SOURCE,
            modifier=1.0,
            target=bid_modifiers.TargetConverter._to_source_target(
                self.source_2.bidder_slug, bid_modifiers.BidModifierType.SOURCE
            ),
        )

        self.ad_group_1.settings.update(None, cpc=decimal.Decimal("1.0"))

    def test_ad_group_cpc_over_limit(self):
        self.ad_group_1.settings.update(None, cpc=decimal.Decimal("12.0"))
        self.ad_group_source_1_1.refresh_from_db()
        self.ad_group_source_1_2.refresh_from_db()
        # no validation error, should be handled by blocker
        self.assertEqual(self.ad_group_source_1_1.settings.local_cpc_cc_proxy, decimal.Decimal("12.0"))
        self.assertEqual(self.ad_group_source_1_2.settings.local_cpc_cc_proxy, decimal.Decimal("12.0"))

    def test_ad_group_cpc_under_limit(self):
        self.ad_group_1.settings.update(None, cpc=decimal.Decimal("0.01"))
        self.ad_group_source_1_1.refresh_from_db()
        self.ad_group_source_1_2.refresh_from_db()
        # no validation error, should be handled by blocker
        self.assertEqual(self.ad_group_source_1_1.settings.local_cpc_cc_proxy, decimal.Decimal("0.01"))
        self.assertEqual(self.ad_group_source_1_2.settings.local_cpc_cc_proxy, decimal.Decimal("0.01"))

    def test_ad_group_cpm_over_limit(self):
        self.ad_group_1.update(None, bidding_type=constants.BiddingType.CPM)
        self.ad_group_1.settings.update(None, cpm=decimal.Decimal("12.0"))
        self.ad_group_source_1_1.refresh_from_db()
        self.ad_group_source_1_2.refresh_from_db()
        # no validation error, should be handled by blocker
        self.assertEqual(self.ad_group_source_1_1.settings.local_cpm_proxy, decimal.Decimal("12.0"))
        self.assertEqual(self.ad_group_source_1_2.settings.local_cpm_proxy, decimal.Decimal("12.0"))

    def test_ad_group_cpm_under_limit(self):
        self.ad_group_1.update(None, bidding_type=constants.BiddingType.CPM)
        self.ad_group_1.settings.update(None, cpm=decimal.Decimal("0.01"))
        self.ad_group_source_1_1.refresh_from_db()
        self.ad_group_source_1_2.refresh_from_db()
        # no validation error, should be handled by blocker
        self.assertEqual(self.ad_group_source_1_1.settings.local_cpm_proxy, decimal.Decimal("0.01"))
        self.assertEqual(self.ad_group_source_1_2.settings.local_cpm_proxy, decimal.Decimal("0.01"))

    def test_ad_group_source_cpc_over_limit(self):
        with self.assertRaises(ags_exceptions.MaximalCPCTooHigh):
            self.ad_group_source_1_1.settings.update(None, cpc_cc=decimal.Decimal("12.0"))

    def test_ad_group_source_cpc_under_limit(self):
        with self.assertRaises(ags_exceptions.MinimalCPCTooLow):
            self.ad_group_source_1_1.settings.update(None, cpc_cc=decimal.Decimal("0.01"))

    def test_ad_group_source_cpm_over_limit(self):
        self.ad_group_1.update(None, bidding_type=constants.BiddingType.CPM)
        with self.assertRaises(ags_exceptions.MaximalCPMTooHigh):
            self.ad_group_source_1_1.settings.update(None, cpm=decimal.Decimal("12.0"))

    def test_ad_group_source_cpm_under_limit(self):
        self.ad_group_1.update(None, bidding_type=constants.BiddingType.CPM)
        with self.assertRaises(ags_exceptions.MinimalCPMTooLow):
            self.ad_group_source_1_1.settings.update(None, cpm=decimal.Decimal("0.01"))

    def test_ad_group_source_cpc_over_limit_via_bid_modifier(self):
        with self.assertRaises(ags_exceptions.MaximalCPCTooHigh):
            bid_modifiers.service.set(
                self.ad_group_1,
                bid_modifiers.BidModifierType.SOURCE,
                bid_modifiers.TargetConverter._to_source_target(
                    self.source_1.bidder_slug, bid_modifiers.BidModifierType.SOURCE
                ),
                None,
                10.5,
            )

    def test_ad_group_source_cpc_under_limit_via_bid_modifier(self):
        with self.assertRaises(ags_exceptions.MinimalCPCTooLow):
            bid_modifiers.service.set(
                self.ad_group_1,
                bid_modifiers.BidModifierType.SOURCE,
                bid_modifiers.TargetConverter._to_source_target(
                    self.source_1.bidder_slug, bid_modifiers.BidModifierType.SOURCE
                ),
                None,
                0.02,
            )


class WorkflowTestCase(TestCase):
    def setUp(self):
        self.source_type = magic_mixer.blend(
            models.SourceType,
            min_cpc=decimal.Decimal("0.01"),
            max_cpc=decimal.Decimal("10.0"),
            min_cpm=decimal.Decimal("0.01"),
            max_cpm=decimal.Decimal("10.0"),
            min_daily_budget=decimal.Decimal("1.0"),
            max_daily_budget=decimal.Decimal("1000.0"),
        )
        self.source = magic_mixer.blend(models.Source, source_type=self.source_type, maintenance=False)
        self.source_credentials = magic_mixer.blend(models.SourceCredentials, source=self.source)
        magic_mixer.blend(
            models.DefaultSourceSettings,
            source=self.source,
            credentials=self.source_credentials,
            default_cpc_cc=decimal.Decimal("0.15"),
            default_mobile_cpc_cc=decimal.Decimal("0.15"),
            default_cpm=decimal.Decimal("1.0"),
            default_mobile_cpm=decimal.Decimal("1.0"),
            default_daily_budget_cc=decimal.Decimal("10.0"),
        )

        self.account = magic_mixer.blend(models.Account)
        self.account.allowed_sources.add(self.source)
        self.campaign = magic_mixer.blend(models.Campaign, account=self.account)

        self.request = magic_mixer.blend_request_user()

    @mock.patch("automation.autopilot_legacy.recalculate_budgets_ad_group")
    def test_create_and_update_ad_group(self, mock_autopilot):
        self.ad_group = models.AdGroup.objects.create(self.request, self.campaign)

        self.ad_group_source = self.ad_group.adgroupsource_set.get(source=self.source)

        self.assertEqual(self.ad_group.bidding_type, constants.BiddingType.CPC)
        self.assertEqual(self.ad_group.settings.cpc, decimal.Decimal("0.45"))
        self.assertEqual(self.ad_group_source.settings.cpc_cc, decimal.Decimal("0.15"))
        self.assertTrue(
            self.ad_group.bidmodifier_set.filter(
                type=bid_modifiers.BidModifierType.SOURCE, target=str(self.source.id)
            ).exists()
        )
        self.assertTrue(
            decimal_helpers.equal_decimals(
                self.ad_group.bidmodifier_set.get(
                    type=bid_modifiers.BidModifierType.SOURCE, target=str(self.source.id)
                ).modifier,
                decimal.Decimal("0.15") / decimal.Decimal("0.45"),
            )
        )

        self.ad_group.settings.update(None, cpc=decimal.Decimal("4.5"))
        self.ad_group_source.refresh_from_db()

        self.assertEqual(self.ad_group.settings.cpc, decimal.Decimal("4.5"))
        self.assertTrue(
            decimal_helpers.equal_decimals(
                self.ad_group.bidmodifier_set.get(
                    type=bid_modifiers.BidModifierType.SOURCE, target=str(self.source.id)
                ).modifier,
                decimal.Decimal("1.5") / decimal.Decimal("4.5"),
            )
        )

    @mock.patch("automation.autopilot_legacy.recalculate_budgets_ad_group")
    def test_create_with_initial_bid(self, mock_autopilot):
        self.ad_group = models.AdGroup.objects.create(
            self.request,
            self.campaign,
            initial_settings={
                "cpc": decimal.Decimal("5.0"),
                "autopilot_state": constants.AdGroupSettingsAutopilotState.INACTIVE,
            },
        )

        self.ad_group_source = self.ad_group.adgroupsource_set.get(source=self.source)

        self.assertEqual(self.ad_group.settings.cpc, decimal.Decimal("5.0"))
        self.assertEqual(self.ad_group_source.settings.cpc_cc, decimal.Decimal("5.0"))
        self.assertFalse(
            self.ad_group.bidmodifier_set.filter(
                type=bid_modifiers.BidModifierType.SOURCE, target=str(self.source.id)
            ).exists()
        )

    @mock.patch("automation.autopilot_legacy.recalculate_budgets_ad_group")
    def test_create_with_initial_bid_over_source_max(self, mock_autopilot):
        self.ad_group = models.AdGroup.objects.create(
            self.request,
            self.campaign,
            initial_settings={
                "cpc": decimal.Decimal("15.0"),
                "autopilot_state": constants.AdGroupSettingsAutopilotState.INACTIVE,
            },
        )

        self.ad_group_source = self.ad_group.adgroupsource_set.get(source=self.source)

        self.assertEqual(self.ad_group.settings.cpc, decimal.Decimal("15.0"))
        self.assertEqual(self.ad_group_source.settings.cpc_cc, decimal.Decimal("15.0"))
        self.assertFalse(
            self.ad_group.bidmodifier_set.filter(
                type=bid_modifiers.BidModifierType.SOURCE, target=str(self.source.id)
            ).exists()
        )

    @mock.patch("automation.autopilot_legacy.recalculate_budgets_ad_group")
    def test_create_with_initial_max_autopilot_bid(self, mock_autopilot):
        self.ad_group = models.AdGroup.objects.create(
            self.request,
            self.campaign,
            initial_settings={
                "max_autopilot_bid": decimal.Decimal("5.0"),
                "autopilot_state": constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,
            },
        )

        self.ad_group_source = self.ad_group.adgroupsource_set.get(source=self.source)

        self.assertEqual(self.ad_group.settings.max_autopilot_bid, decimal.Decimal("5.0"))
        self.assertEqual(self.ad_group.settings.cpc, decimal.Decimal("5.0"))
        self.assertEqual(self.ad_group_source.settings.cpc_cc, decimal.Decimal("5.0"))
        self.assertFalse(
            self.ad_group.bidmodifier_set.filter(
                type=bid_modifiers.BidModifierType.SOURCE, target=str(self.source.id)
            ).exists()
        )

    @mock.patch("automation.autopilot_legacy.recalculate_budgets_ad_group")
    def test_create_with_initial_max_autopilot_bid_no_autopilot(self, mock_autopilot):
        self.ad_group = models.AdGroup.objects.create(
            self.request,
            self.campaign,
            initial_settings={
                "max_autopilot_bid": decimal.Decimal("5.0"),
                "autopilot_state": constants.AdGroupSettingsAutopilotState.INACTIVE,
            },
        )

        self.ad_group_source = self.ad_group.adgroupsource_set.get(source=self.source)

        self.assertEqual(self.ad_group.settings.max_autopilot_bid, decimal.Decimal("5.0"))
        self.assertEqual(self.ad_group.settings.cpc, models.AdGroupSettings.DEFAULT_CPC_VALUE)
        self.assertEqual(self.ad_group_source.settings.cpc_cc, models.AdGroupSettings.DEFAULT_CPC_VALUE)
        self.assertFalse(
            self.ad_group.bidmodifier_set.filter(
                type=bid_modifiers.BidModifierType.SOURCE, target=str(self.source.id)
            ).exists()
        )

    @mock.patch("automation.autopilot_legacy.recalculate_budgets_ad_group")
    def test_reset_source_bid_modifier(self, mock_autopilot):
        self.ad_group = models.AdGroup.objects.create(self.request, self.campaign)

        self.ad_group_source = self.ad_group.adgroupsource_set.get(source=self.source)

        self.assertEqual(self.ad_group.bidding_type, constants.BiddingType.CPC)
        self.assertEqual(self.ad_group.settings.cpc, decimal.Decimal("0.45"))
        self.assertEqual(self.ad_group_source.settings.cpc_cc, decimal.Decimal("0.15"))
        self.assertTrue(
            self.ad_group.bidmodifier_set.filter(
                type=bid_modifiers.BidModifierType.SOURCE, target=str(self.source.id)
            ).exists()
        )
        self.assertTrue(
            decimal_helpers.equal_decimals(
                self.ad_group.bidmodifier_set.get(
                    type=bid_modifiers.BidModifierType.SOURCE, target=str(self.source.id)
                ).modifier,
                decimal.Decimal("0.15") / decimal.Decimal("0.45"),
            )
        )

        bid_modifiers.set(self.ad_group, bid_modifiers.BidModifierType.SOURCE, str(self.source.id), None, 1.0)

        self.assertFalse(
            self.ad_group.bidmodifier_set.filter(
                type=bid_modifiers.BidModifierType.SOURCE, target=str(self.source.id)
            ).exists()
        )
        self.ad_group_source.refresh_from_db()
        self.assertEqual(self.ad_group_source.settings.cpc_cc, decimal.Decimal("0.45"))


class MissingBidModifiersTestCase(TestCase):
    def setUp(self):
        self.ad_group = magic_mixer.blend(models.AdGroup)
        self.ad_group_source_1 = magic_mixer.blend(models.AdGroupSource, ad_group=self.ad_group)
        self.ad_group_source_2 = magic_mixer.blend(models.AdGroupSource, ad_group=self.ad_group)

    def _bid_modifier_qs(self, ad_group_source):
        return self.ad_group.bidmodifier_set.filter(
            type=bid_modifiers.constants.BidModifierType.SOURCE, target=str(ad_group_source.source.id)
        )

    def test_set_ad_group_bid(self):
        self.assertFalse(self._bid_modifier_qs(self.ad_group_source_1).exists())
        self.assertFalse(self._bid_modifier_qs(self.ad_group_source_2).exists())

        self.ad_group.settings.update(None, cpc=decimal.Decimal("1.2000"))
        self.ad_group_source_1.refresh_from_db()
        self.ad_group_source_2.refresh_from_db()

        self.assertEqual(self.ad_group_source_1.settings.local_cpc_cc_proxy, decimal.Decimal("1.2000"))
        self.assertEqual(self.ad_group_source_2.settings.local_cpc_cc_proxy, decimal.Decimal("1.2000"))

        self.assertFalse(self._bid_modifier_qs(self.ad_group_source_1).exists())
        self.assertFalse(self._bid_modifier_qs(self.ad_group_source_2).exists())

    def test_set_ad_group_source_bid(self):
        self.assertFalse(self._bid_modifier_qs(self.ad_group_source_1).exists())
        self.assertFalse(self._bid_modifier_qs(self.ad_group_source_2).exists())

        self.ad_group_source_1.settings.update(None, cpc_cc=(decimal.Decimal("1.5000") * self.ad_group.settings.cpc))
        self.ad_group_source_1.refresh_from_db()
        self.ad_group_source_2.refresh_from_db()

        self.assertEqual(self.ad_group_source_1.settings.cpc_cc, decimal.Decimal("1.5000") * self.ad_group.settings.cpc)
        self.assertEqual(self.ad_group_source_2.settings.cpc_cc, None)

        self.assertTrue(self._bid_modifier_qs(self.ad_group_source_1).exists())
        self.assertFalse(self._bid_modifier_qs(self.ad_group_source_2).exists())

        self.assertEquals(self._bid_modifier_qs(self.ad_group_source_1).first().modifier, 1.5)


class AllRTBUpdateTestCase(TestCase):
    def setUp(self):
        magic_mixer.blend(
            models.CurrencyExchangeRate,
            currency=constants.Currency.EUR,
            date=dates_helper.local_today(),
            exchange_rate=decimal.Decimal("0.8968"),
        )

        self.ad_group = magic_mixer.blend(
            models.AdGroup,
            bidding_type=constants.BiddingType.CPC,
            campaign__account__currency=constants.Currency.EUR,
            campaign__account__agency__uses_realtime_autopilot=True,
        )

    def _setup_ad_group_and_sources(self, ad_group_settings, ad_group_source_settings_1, ad_group_source_settings_2):
        self.ad_group.settings.update_unsafe(None, **ad_group_settings)

        self.ad_group_source_1 = magic_mixer.blend(
            models.AdGroupSource, ad_group=self.ad_group, source__source_type__type=constants.SourceType.OUTBRAIN
        )
        self.ad_group_source_2 = magic_mixer.blend(
            models.AdGroupSource, ad_group=self.ad_group, source__source_type__type=constants.SourceType.B1
        )

        self.ad_group_source_1.settings.update_unsafe(None, **ad_group_source_settings_1)
        self.ad_group_source_2.settings.update_unsafe(None, **ad_group_source_settings_2)

    def _initial_ad_group_settings(self, **updates):
        settings = {
            "cpc": decimal.Decimal("20.0000"),
            "local_cpc": decimal.Decimal("17.9360"),
            "cpm": decimal.Decimal("25.0000"),
            "local_cpm": decimal.Decimal("22.4200"),
            "b1_sources_group_cpc_cc": decimal.Decimal("0.2230"),
            "local_b1_sources_group_cpc_cc": decimal.Decimal("0.2000"),
            "b1_sources_group_cpm": decimal.Decimal("0.0096"),
            "local_b1_sources_group_cpm": decimal.Decimal("0.0086"),
            "b1_sources_group_enabled": True,
        }
        settings.update(updates)
        return settings

    def _initial_ad_group_source_settings(self, **updates):
        settings = {
            "cpc_cc": decimal.Decimal("0.2230"),
            "local_cpc_cc": decimal.Decimal("0.2000"),
            "cpm": decimal.Decimal("0.9852"),
            "local_cpm": decimal.Decimal("0.8835"),
        }
        settings.update(updates)
        return settings

    def _assert_ad_group_state(self, settings):
        for k, v in settings.items():
            self.assertEqual(
                getattr(self.ad_group.settings, k),
                v,
                "{}: expected {}, got {}".format(k, v, getattr(self.ad_group.settings, k)),
            )

    def _assert_source_bid_modifier(self, ad_group_source, bid_modifier_value):
        self.assertAlmostEqual(
            self.ad_group.bidmodifier_set.get(
                type=bid_modifiers.BidModifierType.SOURCE, target=str(ad_group_source.source.id)
            ).modifier,
            bid_modifier_value,
            places=8,
        )

    def test_manual_b1_sources_group_update(self):
        # manual setting of b1 sources group value is disabled in dashboard, but is still available through API
        ad_group_settings = self._initial_ad_group_settings()
        ad_group_settings.update({"autopilot_state": constants.AdGroupSettingsAutopilotState.INACTIVE})
        ad_group_source_settings = self._initial_ad_group_source_settings()
        self._setup_ad_group_and_sources(ad_group_settings, ad_group_source_settings, ad_group_source_settings)

        sbm_1 = bid_modifiers.BidModifier.objects.get(
            ad_group=self.ad_group,
            type=bid_modifiers.BidModifierType.SOURCE,
            target=str(self.ad_group_source_1.source.id),
        ).modifier
        sbm_2 = bid_modifiers.BidModifier.objects.get(
            ad_group=self.ad_group,
            type=bid_modifiers.BidModifierType.SOURCE,
            target=str(self.ad_group_source_2.source.id),
        ).modifier

        self.ad_group.settings.update(None, b1_sources_group_cpc_cc=decimal.Decimal("0.4000"))

        self.ad_group.refresh_from_db()
        self.ad_group_source_1.refresh_from_db()
        self.ad_group_source_2.refresh_from_db()

        self._assert_ad_group_state(
            {
                "cpc": decimal.Decimal("0.4000"),
                "local_cpc": decimal.Decimal("0.3587"),
                "b1_sources_group_cpc_cc": decimal.Decimal("0.4000"),
                "local_b1_sources_group_cpc_cc": decimal.Decimal("0.3587"),
            }
        )

        self._assert_source_bid_modifier(self.ad_group_source_1, sbm_1)

        self._assert_source_bid_modifier(self.ad_group_source_2, sbm_2)

    def test_manual_ad_group_cpc_update(self):
        ad_group_settings = self._initial_ad_group_settings()
        ad_group_settings.update({"autopilot_state": constants.AdGroupSettingsAutopilotState.INACTIVE})
        ad_group_source_settings = self._initial_ad_group_source_settings()
        self._setup_ad_group_and_sources(ad_group_settings, ad_group_source_settings, ad_group_source_settings)

        sbm_1 = bid_modifiers.BidModifier.objects.get(
            ad_group=self.ad_group,
            type=bid_modifiers.BidModifierType.SOURCE,
            target=str(self.ad_group_source_1.source.id),
        ).modifier
        sbm_2 = bid_modifiers.BidModifier.objects.get(
            ad_group=self.ad_group,
            type=bid_modifiers.BidModifierType.SOURCE,
            target=str(self.ad_group_source_2.source.id),
        ).modifier

        self.ad_group.settings.update(None, cpc=decimal.Decimal("15.0000"))

        self.ad_group.refresh_from_db()
        self.ad_group_source_1.refresh_from_db()
        self.ad_group_source_2.refresh_from_db()

        self._assert_ad_group_state(
            {
                "cpc": decimal.Decimal("15.0000"),
                "local_cpc": decimal.Decimal("13.4520"),
                "b1_sources_group_cpc_cc": decimal.Decimal("15.0000"),
                "local_b1_sources_group_cpc_cc": decimal.Decimal("13.4520"),
            }
        )

        self._assert_source_bid_modifier(self.ad_group_source_1, sbm_1)

        self._assert_source_bid_modifier(self.ad_group_source_2, sbm_2)

    def test_manual_b1_sources_group_bid_update_outside_limits(self):
        ad_group_settings = self._initial_ad_group_settings(b1_sources_group_enabled=False)
        ad_group_settings.update({"autopilot_state": constants.AdGroupSettingsAutopilotState.INACTIVE})
        ad_group_source_settings = self._initial_ad_group_source_settings()
        self._setup_ad_group_and_sources(ad_group_settings, ad_group_source_settings, ad_group_source_settings)

        with self.assertRaises(utils.exc.MultipleValidationError) as err:
            self.ad_group.settings.update(
                None, b1_sources_group_enabled=True, local_b1_sources_group_cpc_cc=decimal.Decimal("91.0000")
            )
        self.assertCountEqual([type(e) for e in err.exception.errors], [ag_exceptions.CPCTooHigh])

        with self.assertRaises(utils.exc.MultipleValidationError) as err:
            self.ad_group.settings.update(
                None, b1_sources_group_enabled=True, local_b1_sources_group_cpc_cc=decimal.Decimal("0.0010")
            )
        self.assertCountEqual([type(e) for e in err.exception.errors], [ag_exceptions.CPCTooLow])

        self.ad_group.bidding_type = constants.BiddingType.CPM
        self.ad_group.save(None)

        with self.assertRaises(utils.exc.MultipleValidationError) as err:
            self.ad_group.settings.update(
                None, b1_sources_group_enabled=True, local_b1_sources_group_cpm=decimal.Decimal("91.0000")
            )
        self.assertCountEqual([type(e) for e in err.exception.errors], [ag_exceptions.CPMTooHigh])

        with self.assertRaises(utils.exc.MultipleValidationError) as err:
            self.ad_group.settings.update(
                None, b1_sources_group_enabled=True, local_b1_sources_group_cpm=decimal.Decimal("0.0010")
            )
        self.assertCountEqual([type(e) for e in err.exception.errors], [ag_exceptions.CPMTooLow])


class MulticurrencyUpdateTestCase(TestCase):
    def test_recalculate_ad_group_amounts(self):
        magic_mixer.blend(
            models.CurrencyExchangeRate,
            currency=constants.Currency.EUR,
            date=dates_helper.local_today() - timedelta(days=1),
            exchange_rate=decimal.Decimal("0.8968"),
        )

        ad_group = magic_mixer.blend(
            models.AdGroup, bidding_type=constants.BiddingType.CPC, campaign__account__currency=constants.Currency.EUR
        )
        ad_group.campaign.settings.update_unsafe(None, autopilot=False)

        ad_group.settings.update_unsafe(
            None,
            cpc=decimal.Decimal("20.0000"),
            local_cpc=decimal.Decimal("17.9360"),
            cpm=decimal.Decimal("25.0000"),
            local_cpm=decimal.Decimal("22.4200"),
            b1_sources_group_cpc_cc=decimal.Decimal("0.2230"),
            local_b1_sources_group_cpc_cc=decimal.Decimal("0.2000"),
            b1_sources_group_cpm=decimal.Decimal("0.0096"),
            local_b1_sources_group_cpm=decimal.Decimal("0.0086"),
            b1_sources_group_enabled=True,
            autopilot_state=constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,
        )

        ad_group_source_1 = magic_mixer.blend(models.AdGroupSource, ad_group=ad_group)
        ad_group_source_2 = magic_mixer.blend(
            models.AdGroupSource, ad_group=ad_group, source__source_type__type=constants.SourceType.B1
        )

        ad_group_source_1.settings.update_unsafe(
            None,
            cpc_cc=decimal.Decimal("0.2230"),
            local_cpc_cc=decimal.Decimal("0.2000"),
            cpm=decimal.Decimal("0.9852"),
            local_cpm=decimal.Decimal("0.8835"),
        )
        ad_group_source_2.settings.update_unsafe(
            None,
            cpc_cc=decimal.Decimal("0.2230"),
            local_cpc_cc=decimal.Decimal("0.2000"),
            cpm=decimal.Decimal("0.9852"),
            local_cpm=decimal.Decimal("0.8835"),
        )

        self.assertEqual(ad_group.settings.cpc, decimal.Decimal("20.0000"))
        self.assertEqual(ad_group.settings.local_cpc, decimal.Decimal("17.9360"))
        self.assertEqual(ad_group.settings.b1_sources_group_cpc_cc, decimal.Decimal("0.2230"))
        self.assertEqual(ad_group.settings.local_b1_sources_group_cpc_cc, decimal.Decimal("0.2000"))

        self.assertEqual(ad_group_source_1.settings.cpc_cc, decimal.Decimal("0.2230"))
        self.assertEqual(ad_group_source_1.settings.local_cpc_cc, decimal.Decimal("0.2000"))
        self.assertEqual(ad_group_source_2.settings.cpc_cc, decimal.Decimal("0.2230"))
        self.assertEqual(ad_group_source_2.settings.local_cpc_cc, decimal.Decimal("0.2000"))

        self.assertAlmostEqual(
            ad_group.bidmodifier_set.get(
                type=bid_modifiers.BidModifierType.SOURCE, target=str(ad_group_source_1.source.id)
            ).modifier,
            float(decimal.Decimal("0.2230") / decimal.Decimal("20.0000")),
            places=8,
        )
        self.assertAlmostEqual(
            ad_group.bidmodifier_set.get(
                type=bid_modifiers.BidModifierType.SOURCE, target=str(ad_group_source_2.source.id)
            ).modifier,
            float(decimal.Decimal("0.2230") / decimal.Decimal("20.0000")),
            places=8,
        )

        magic_mixer.blend(
            models.CurrencyExchangeRate,
            currency=constants.Currency.EUR,
            date=dates_helper.local_today(),
            exchange_rate=decimal.Decimal("0.9061"),
        )

        _recalculate_ad_group_amounts(ad_group.campaign)

        ad_group.refresh_from_db()
        ad_group_source_1.refresh_from_db()
        ad_group_source_2.refresh_from_db()

        self.assertEqual(ad_group.settings.cpc, decimal.Decimal("19.7947"))
        self.assertEqual(ad_group.settings.local_cpc, decimal.Decimal("17.9360"))
        self.assertEqual(ad_group.settings.b1_sources_group_cpc_cc, decimal.Decimal("0.2207"))
        self.assertEqual(ad_group.settings.local_b1_sources_group_cpc_cc, decimal.Decimal("0.2000"))

        self.assertEqual(ad_group_source_1.settings.cpc_cc, decimal.Decimal("0.2207"))
        self.assertEqual(ad_group_source_1.settings.local_cpc_cc, decimal.Decimal("0.2000"))
        self.assertEqual(ad_group_source_2.settings.cpc_cc, decimal.Decimal("0.2207"))
        self.assertEqual(ad_group_source_2.settings.local_cpc_cc, decimal.Decimal("0.2000"))

        self.assertAlmostEqual(
            ad_group.bidmodifier_set.get(
                type=bid_modifiers.BidModifierType.SOURCE, target=str(ad_group_source_1.source.id)
            ).modifier,
            float(decimal.Decimal("0.2207") / decimal.Decimal("19.7947")),
            places=8,
        )
        self.assertAlmostEqual(
            ad_group.bidmodifier_set.get(
                type=bid_modifiers.BidModifierType.SOURCE, target=str(ad_group_source_2.source.id)
            ).modifier,
            float(decimal.Decimal("0.2207") / decimal.Decimal("19.7947")),
            places=8,
        )

    def test_recalculate_ad_group_amounts_limits(self):
        magic_mixer.blend(
            models.CurrencyExchangeRate,
            currency=constants.Currency.EUR,
            date=dates_helper.local_today() - timedelta(days=1),
            exchange_rate=decimal.Decimal("0.8968"),
        )

        account = magic_mixer.blend(models.Account, currency=constants.Currency.EUR)
        campaign = magic_mixer.blend(models.Campaign, account=account)
        ad_group_1 = magic_mixer.blend(models.AdGroup, campaign=campaign, bidding_type=constants.BiddingType.CPC)

        ad_group_2 = magic_mixer.blend(models.AdGroup, campaign=campaign, bidding_type=constants.BiddingType.CPC)

        ad_group_1.settings.update_unsafe(
            None,
            cpc=decimal.Decimal("20.0000"),
            local_cpc=decimal.Decimal("17.9360"),
            cpm=decimal.Decimal("25.0000"),
            local_cpm=decimal.Decimal("22.4200"),
            autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE,
        )

        ad_group_2.settings.update_unsafe(
            None,
            cpc=decimal.Decimal("10.0000"),
            local_cpc=decimal.Decimal("8.9680"),
            cpm=decimal.Decimal("12.5000"),
            local_cpm=decimal.Decimal("11.2100"),
            autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE,
        )

        self.assertEqual(ad_group_1.settings.cpc, decimal.Decimal("20.0000"))
        self.assertEqual(ad_group_1.settings.local_cpc, decimal.Decimal("17.9360"))
        self.assertEqual(ad_group_1.settings.cpm, decimal.Decimal("25.0000"))
        self.assertEqual(ad_group_1.settings.local_cpm, decimal.Decimal("22.4200"))

        self.assertEqual(ad_group_2.settings.cpc, decimal.Decimal("10.0000"))
        self.assertEqual(ad_group_2.settings.local_cpc, decimal.Decimal("8.9680"))
        self.assertEqual(ad_group_2.settings.cpm, decimal.Decimal("12.5000"))
        self.assertEqual(ad_group_2.settings.local_cpm, decimal.Decimal("11.2100"))

        magic_mixer.blend(
            models.CurrencyExchangeRate,
            currency=constants.Currency.EUR,
            date=dates_helper.local_today(),
            exchange_rate=decimal.Decimal("0.9061"),
        )

        _recalculate_ad_group_amounts(campaign)

        ad_group_1.refresh_from_db()
        ad_group_2.refresh_from_db()

        self.assertEqual(ad_group_1.settings.cpc, decimal.Decimal("19.7947"))
        self.assertEqual(ad_group_1.settings.local_cpc, decimal.Decimal("17.9360"))
        self.assertEqual(ad_group_1.settings.cpm, decimal.Decimal("24.7434"))
        self.assertEqual(ad_group_1.settings.local_cpm, decimal.Decimal("22.4200"))

        self.assertEqual(ad_group_2.settings.cpc, decimal.Decimal("9.8974"))
        self.assertEqual(ad_group_2.settings.local_cpc, decimal.Decimal("8.9680"))
        self.assertEqual(ad_group_2.settings.cpm, decimal.Decimal("12.3717"))
        self.assertEqual(ad_group_2.settings.local_cpm, decimal.Decimal("11.2100"))


class SkipSourceValidationTestCase(TestCase):
    def test_minimal_cpc_too_low(self):
        source_type = magic_mixer.blend(models.SourceType, max_cpc="3.0000", min_cpc="0.500")
        source = magic_mixer.blend(models.Source, source_type=source_type)

        ad_group = magic_mixer.blend(models.AdGroup, bidding_type=constants.BiddingType.CPC)
        ad_group_source = magic_mixer.blend(models.AdGroupSource, source=source, ad_group=ad_group)

        ad_group.settings.update_unsafe(
            None,
            cpc=decimal.Decimal("2.0000"),
            local_cpc=decimal.Decimal("1.0000"),
            cpm=decimal.Decimal("2.0000"),
            local_cpm=decimal.Decimal("1.0000"),
            autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE,
        )

        ad_group_source.settings.update_unsafe(
            None,
            cpc_cc=decimal.Decimal("0.5000"),
            local_cpc_cc=decimal.Decimal("0.2500"),
            cpm=decimal.Decimal("0.5000"),
            local_cpm=decimal.Decimal("0.2500"),
        )

        target_source_cpc = decimal.Decimal("0.1000")
        # must not raise MinimaCPCTooLow
        bm = bid_modifiers.create_source_bid_modifier_data(source, ad_group.settings.cpc, target_source_cpc)
        bid_modifiers.set_bulk(
            ad_group, [bm], user=None, write_history=False, propagate_to_k1=False, skip_validation=True
        )

        ad_group_source.refresh_from_db()

        self.assertEqual(ad_group_source.settings.cpc_cc, target_source_cpc)
        self.assertEqual(
            ad_group.bidmodifier_set.filter(type=bid_modifiers.BidModifierType.SOURCE, target=str(source.id))
            .get()
            .modifier,
            float(target_source_cpc / ad_group.settings.cpc),
        )

    def test_minimal_cpc_too_high(self):
        source_type = magic_mixer.blend(models.SourceType, max_cpc="3.0000", min_cpc="0.500")
        source = magic_mixer.blend(models.Source, source_type=source_type)

        ad_group = magic_mixer.blend(models.AdGroup, bidding_type=constants.BiddingType.CPC)
        ad_group_source = magic_mixer.blend(models.AdGroupSource, source=source, ad_group=ad_group)

        ad_group.settings.update_unsafe(
            None,
            cpc=decimal.Decimal("2.0000"),
            local_cpc=decimal.Decimal("1.0000"),
            cpm=decimal.Decimal("2.0000"),
            local_cpm=decimal.Decimal("1.0000"),
            autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE,
        )

        ad_group_source.settings.update_unsafe(
            None,
            cpc_cc=decimal.Decimal("0.5000"),
            local_cpc_cc=decimal.Decimal("0.2500"),
            cpm=decimal.Decimal("0.5000"),
            local_cpm=decimal.Decimal("0.2500"),
        )

        target_source_cpc = decimal.Decimal("4.0000")
        # must not raise MinimaCPCTooHigh
        bm = bid_modifiers.create_source_bid_modifier_data(source, ad_group.settings.cpc, target_source_cpc)
        bid_modifiers.set_bulk(
            ad_group, [bm], user=None, write_history=False, propagate_to_k1=False, skip_validation=True
        )

        ad_group_source.refresh_from_db()

        self.assertEqual(ad_group_source.settings.cpc_cc, target_source_cpc)
        self.assertEqual(
            ad_group.bidmodifier_set.filter(type=bid_modifiers.BidModifierType.SOURCE, target=str(source.id))
            .get()
            .modifier,
            float(target_source_cpc / ad_group.settings.cpc),
        )


class MaxAutopilotBidTestCase(TestCase):
    def setUp(self):
        self.source_type_1 = magic_mixer.blend(
            models.SourceType,
            min_cpc=decimal.Decimal("0.01"),
            max_cpc=decimal.Decimal("10.0"),
            min_cpm=decimal.Decimal("0.01"),
            max_cpm=decimal.Decimal("10.0"),
        )
        self.source_type_2 = magic_mixer.blend(
            models.SourceType,
            min_cpc=decimal.Decimal("0.01"),
            max_cpc=decimal.Decimal("15.0"),
            min_cpm=decimal.Decimal("0.01"),
            max_cpm=decimal.Decimal("15.0"),
        )

        self.source_1 = magic_mixer.blend(models.Source, source_type=self.source_type_1, maintenance=False)
        self.source_2 = magic_mixer.blend(models.Source, source_type=self.source_type_2, maintenance=False)

        self.source_credentials_1 = magic_mixer.blend(models.SourceCredentials, source=self.source_1)
        self.source_credentials_2 = magic_mixer.blend(models.SourceCredentials, source=self.source_2)

        magic_mixer.blend(
            models.DefaultSourceSettings,
            source=self.source_1,
            credentials=self.source_credentials_1,
            default_cpc_cc=decimal.Decimal("0.15"),
            default_mobile_cpc_cc=decimal.Decimal("0.15"),
            default_cpm=decimal.Decimal("1.0"),
            default_mobile_cpm=decimal.Decimal("1.0"),
            default_daily_budget_cc=decimal.Decimal("10.0"),
        )
        magic_mixer.blend(
            models.DefaultSourceSettings,
            source=self.source_2,
            credentials=self.source_credentials_2,
            default_cpc_cc=decimal.Decimal("0.45"),
            default_mobile_cpc_cc=decimal.Decimal("0.45"),
            default_cpm=decimal.Decimal("1.0"),
            default_mobile_cpm=decimal.Decimal("1.0"),
            default_daily_budget_cc=decimal.Decimal("10.0"),
        )

        self.account = magic_mixer.blend(models.Account)
        self.account.allowed_sources.add(self.source_1, self.source_2)
        self.campaign = magic_mixer.blend(models.Campaign, account=self.account)

        self.request = magic_mixer.blend_request_user()

    @mock.patch("automation.autopilot_legacy.recalculate_budgets_ad_group")
    def test_enable_full_autopilot_cpc(self, mock_autopilot):
        self._init_ad_group(constants.BiddingType.CPC)

        self.ad_group.settings.update(
            None,
            autopilot_state=constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,
            max_autopilot_bid=decimal.Decimal("3.0"),
        )

        self.ad_group_source_1.refresh_from_db()
        self.ad_group_source_2.refresh_from_db()

        self.assertEqual(self.ad_group.settings.cpc, decimal.Decimal("3.0"))
        self.assertEqual(self.ad_group_source_1.settings.local_cpc_cc_proxy, decimal.Decimal("3.0"))
        self.assertEqual(self.ad_group_source_2.settings.local_cpc_cc_proxy, decimal.Decimal("3.0"))

    @mock.patch("automation.autopilot_legacy.recalculate_budgets_ad_group")
    def test_enable_bid_autopilot_cpc(self, mock_autopilot):
        self._init_ad_group(constants.BiddingType.CPC)
        self.ad_group.settings.update(
            None,
            autopilot_state=constants.AdGroupSettingsAutopilotState.ACTIVE_CPC,
            max_autopilot_bid=decimal.Decimal("3.0"),
        )

        self.ad_group_source_1.refresh_from_db()
        self.ad_group_source_2.refresh_from_db()

        # changing max autopilot bid changes cpc
        self.assertEqual(self.ad_group.settings.cpc, decimal.Decimal("3.0"))
        self.assertEqual(self.ad_group_source_1.settings.local_cpc_cc_proxy, decimal.Decimal("3.0"))
        self.assertEqual(self.ad_group_source_2.settings.local_cpc_cc_proxy, decimal.Decimal("3.0"))

    @mock.patch("automation.autopilot_legacy.recalculate_budgets_ad_group")
    def test_disable_autopilot_increase_cpc(self, mock_autopilot):
        self._init_ad_group(constants.BiddingType.CPC)
        self.ad_group.settings.update(
            None,
            autopilot_state=constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,
            max_autopilot_bid=decimal.Decimal("3.0"),
        )
        self.ad_group.settings.update(
            None, autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE, cpc=decimal.Decimal("20.0")
        )

        self.ad_group_source_1.refresh_from_db()
        self.ad_group_source_2.refresh_from_db()

        self.assertEqual(self.ad_group.settings.cpc, decimal.Decimal("20.0"))
        self.assertEqual(self.ad_group_source_1.settings.local_cpc_cc_proxy, decimal.Decimal("20.0"))
        self.assertEqual(self.ad_group_source_2.settings.local_cpc_cc_proxy, decimal.Decimal("20.0"))

    @mock.patch("automation.autopilot_legacy.recalculate_budgets_ad_group")
    def test_increase_max_autopilot_bid_cpc_bid_modifier_resets(self, mock_autopilot):
        self._init_ad_group(constants.BiddingType.CPC)
        self.ad_group.settings.update(
            None,
            autopilot_state=constants.AdGroupSettingsAutopilotState.ACTIVE_CPC,
            max_autopilot_bid=decimal.Decimal("10.0"),
        )

        bid_modifier_1 = magic_mixer.blend(
            models.BidModifier,
            ad_group=self.ad_group,
            type=bid_modifiers.BidModifierType.SOURCE,
            modifier=0.3,
            target=bid_modifiers.TargetConverter._to_source_target(
                self.ad_group_source_1.source.bidder_slug, bid_modifiers.BidModifierType.SOURCE
            ),
        )
        self.ad_group.settings.update(
            None,
            autopilot_state=constants.AdGroupSettingsAutopilotState.ACTIVE_CPC,
            max_autopilot_bid=decimal.Decimal("15.0"),
        )

        self.ad_group_source_1.refresh_from_db()
        self.ad_group_source_2.refresh_from_db()

        with self.assertRaises(models.BidModifier.DoesNotExist):
            # was reset because max autopilot bid changed
            bid_modifier_1.refresh_from_db()

        # changing max autopilot bid changes cpc
        self.assertEqual(self.ad_group.settings.cpc, decimal.Decimal("15.0"))
        self.assertEqual(self.ad_group_source_1.settings.local_cpc_cc_proxy, decimal.Decimal("15.0"))
        self.assertEqual(self.ad_group_source_2.settings.local_cpc_cc_proxy, decimal.Decimal("15.0"))

    @mock.patch("automation.autopilot_legacy.recalculate_budgets_ad_group")
    def test_max_autopilot_bid_to_unlimited(self, mock_autopilot):
        self._init_ad_group(constants.BiddingType.CPC)
        self.ad_group.settings.update(
            None,
            autopilot_state=constants.AdGroupSettingsAutopilotState.ACTIVE_CPC,
            max_autopilot_bid=decimal.Decimal("10.0"),
        )

        bid_modifier_1 = magic_mixer.blend(
            models.BidModifier,
            ad_group=self.ad_group,
            type=bid_modifiers.BidModifierType.SOURCE,
            modifier=0.3,
            target=bid_modifiers.TargetConverter._to_source_target(
                self.ad_group_source_1.source.bidder_slug, bid_modifiers.BidModifierType.SOURCE
            ),
        )
        self.ad_group.settings.update(
            None, autopilot_state=constants.AdGroupSettingsAutopilotState.ACTIVE_CPC, max_autopilot_bid=None
        )

        self.ad_group_source_1.refresh_from_db()
        self.ad_group_source_2.refresh_from_db()

        bid_modifier_1.refresh_from_db()
        self.assertEqual(bid_modifier_1.modifier, 0.3)

        self.assertEqual(self.ad_group.settings.max_autopilot_bid, None)
        self.assertEqual(self.ad_group.settings.cpc, decimal.Decimal("10.0"))
        self.assertEqual(self.ad_group_source_1.settings.local_cpc_cc_proxy, decimal.Decimal("3.0"))
        self.assertEqual(self.ad_group_source_2.settings.local_cpc_cc_proxy, decimal.Decimal("10.0"))

    @mock.patch("automation.autopilot_legacy.recalculate_budgets_ad_group")
    def test_disable_autopilot_cpm(self, mock_autopilot):
        self._init_ad_group(constants.BiddingType.CPM)
        self.ad_group.settings.update(
            None, autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE, cpm=decimal.Decimal("20.0")
        )

        self.ad_group_source_1.refresh_from_db()
        self.ad_group_source_2.refresh_from_db()

        self.assertEqual(self.ad_group_source_2.settings.local_cpm_proxy, decimal.Decimal("20.0"))
        self.assertEqual(self.ad_group_source_1.settings.local_cpm_proxy, decimal.Decimal("20.0"))

    @mock.patch("automation.autopilot_legacy.recalculate_budgets_ad_group")
    def test_enable_full_autopilot_cpm(self, mock_autopilot):
        self._init_ad_group(constants.BiddingType.CPM)
        self.ad_group.settings.update(
            None,
            autopilot_state=constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,
            max_autopilot_bid=decimal.Decimal("3.0"),
        )

        self.ad_group_source_1.refresh_from_db()
        self.ad_group_source_2.refresh_from_db()

        self.assertEqual(self.ad_group.settings.cpm, decimal.Decimal("3.0"))
        self.assertEqual(self.ad_group_source_1.settings.local_cpm_proxy, decimal.Decimal("3.0"))
        self.assertEqual(self.ad_group_source_2.settings.local_cpm_proxy, decimal.Decimal("3.0"))

    @mock.patch("automation.autopilot_legacy.recalculate_budgets_ad_group")
    def test_enable_bid_autopilot_cpm(self, mock_autopilot):
        self._init_ad_group(constants.BiddingType.CPM)
        self.ad_group.settings.update(
            None,
            autopilot_state=constants.AdGroupSettingsAutopilotState.ACTIVE_CPC,
            max_autopilot_bid=decimal.Decimal("3.0"),
        )

        self.ad_group_source_1.refresh_from_db()
        self.ad_group_source_2.refresh_from_db()

        # changing max autopilot bid changes cpm
        self.assertEqual(self.ad_group.settings.cpm, decimal.Decimal("3.0"))
        self.assertEqual(self.ad_group_source_1.settings.local_cpm_proxy, decimal.Decimal("3.0"))
        self.assertEqual(self.ad_group_source_2.settings.local_cpm_proxy, decimal.Decimal("3.0"))

    @mock.patch("automation.autopilot_legacy.recalculate_budgets_ad_group")
    def test_increase_max_autopilot_bid_reset_bid_modifier(self, mock_autopilot):
        self._init_ad_group(constants.BiddingType.CPM)
        self.ad_group.settings.update(
            None,
            max_autopilot_bid=decimal.Decimal("10.0"),
            autopilot_state=constants.AdGroupSettingsAutopilotState.ACTIVE_CPC,
        )

        bid_modifier_1 = magic_mixer.blend(
            models.BidModifier,
            ad_group=self.ad_group,
            type=bid_modifiers.BidModifierType.SOURCE,
            modifier=0.3,
            target=bid_modifiers.TargetConverter._to_source_target(
                self.ad_group_source_1.source.bidder_slug, bid_modifiers.BidModifierType.SOURCE
            ),
        )
        self.ad_group.settings.update(None, max_autopilot_bid=decimal.Decimal("15.0"))

        self.ad_group_source_1.refresh_from_db()
        self.ad_group_source_2.refresh_from_db()

        with self.assertRaises(models.BidModifier.DoesNotExist):
            # was reset because max autopilot bid changed
            bid_modifier_1.refresh_from_db()

        # changing max autopilot bid changes cpm
        self.assertEqual(self.ad_group.settings.cpm, decimal.Decimal("15.0"))
        self.assertEqual(self.ad_group_source_1.settings.local_cpm_proxy, decimal.Decimal("15.0"))
        self.assertEqual(self.ad_group_source_2.settings.local_cpm_proxy, decimal.Decimal("15.0"))

    def _init_ad_group(self, bidding_type):
        initial_bid = decimal.Decimal("5.0")
        bid_field = "cpc" if bidding_type == constants.BiddingType.CPC else "cpm"
        initial_settings = {"autopilot_state": constants.AdGroupSettingsAutopilotState.INACTIVE, bid_field: initial_bid}

        self.ad_group = models.AdGroup.objects.create(
            self.request, self.campaign, bidding_type=bidding_type, initial_settings=initial_settings
        )

        self.ad_group_source_1 = self.ad_group.adgroupsource_set.get(source=self.source_1)
        self.ad_group_source_2 = self.ad_group.adgroupsource_set.get(source=self.source_2)

        ad_group_source_bid_field = "cpc_cc" if bidding_type == constants.BiddingType.CPC else "cpm"
        self.assertEqual(getattr(self.ad_group_source_1.settings, ad_group_source_bid_field), initial_bid)
        self.assertEqual(getattr(self.ad_group_source_2.settings, ad_group_source_bid_field), initial_bid)
