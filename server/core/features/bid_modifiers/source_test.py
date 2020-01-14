import decimal
from datetime import timedelta

import mock
from django.test import TestCase

import core.features.multicurrency
from automation.autopilot import helpers as autopilot_helpers
from core.features import bid_modifiers
from core.features.multicurrency.service.update import _recalculate_ad_group_amounts
from core.models.settings.ad_group_source_settings import exceptions as ags_exceptions
from dash import constants
from dash import models
from utils import dates_helper
from utils import decimal_helpers
from utils.magic_mixer import magic_mixer


class SourceBidValidationMixin(object):
    def setUp(self):
        self.request = magic_mixer.blend_request_user(["fea_can_use_cpm_buying"])
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
                target=bid_modifiers.TargetConverter._to_source_target(ad_group_source.source.bidder_slug),
            )
            ad_group_source.settings.update(None, **{source_bid_value_attr: decimal.Decimal(modifier) * bid_value})

    def _get_source_bid_modifier(self, ad_group_source):
        return models.BidModifier.objects.get(
            ad_group=self.ad_group,
            type=bid_modifiers.BidModifierType.SOURCE,
            target=bid_modifiers.TargetConverter._to_source_target(ad_group_source.source.bidder_slug),
        )

    def _assert_bid_modifiers(self, expected_bid_modifiers_list):
        output_bid_modifiers_list = list(
            self.ad_group.bidmodifier_set.filter(type=bid_modifiers.BidModifierType.SOURCE)
            .order_by("id")
            .values_list("modifier", flat=True)
        )
        self.assertEqual(output_bid_modifiers_list, expected_bid_modifiers_list)

    def _assert_source_bid_values(self, bidding_type, expected_bid_value_list):
        attribute = "settings__cpc_cc" if bidding_type == constants.BiddingType.CPC else "settings__cpm"
        output_bid_value_list = list(self.ad_group.adgroupsource_set.order_by("id").values_list(attribute, flat=True))

        self.assertEqual(output_bid_value_list, expected_bid_value_list)

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
        self._assert_source_bid_values(constants.BiddingType.CPC, [decimal.Decimal("0.06"), decimal.Decimal("0.28")])

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
                [
                    ["Source", 'CPC set from "$0.140" to "$0.280"'],
                    {
                        "action_type": constants.HistoryActionType.SETTINGS_CHANGE,
                        "changes": {"local_cpc_cc": decimal.Decimal("0.2800")},
                        "system_user": None,
                        "user": None,
                    },
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
        self._assert_source_bid_values(constants.BiddingType.CPM, [decimal.Decimal("0.6"), decimal.Decimal("2.8")])

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
                [
                    ["Source", 'CPM set from "$1.400" to "$2.800"'],
                    {
                        "action_type": constants.HistoryActionType.SETTINGS_CHANGE,
                        "changes": {"local_cpm": decimal.Decimal("2.8000")},
                        "system_user": None,
                        "user": None,
                    },
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
        self._assert_source_bid_values(constants.BiddingType.CPC, [decimal.Decimal("0.06"), decimal.Decimal("0.3")])

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
        self._assert_source_bid_values(constants.BiddingType.CPM, [decimal.Decimal("0.6"), decimal.Decimal("3.0")])

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
        self._assert_source_bid_values(constants.BiddingType.CPC, [decimal.Decimal("0.06"), decimal.Decimal("0.3")])

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
        self._assert_source_bid_values(constants.BiddingType.CPM, [decimal.Decimal("0.6"), decimal.Decimal("3.0")])

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
                target=bid_modifiers.TargetConverter._to_source_target(ad_group_source.source.bidder_slug),
            )
            ad_group_source.settings.update_unsafe(None, cpc_cc=source_cpc, cpm=source_cpm)

    def test_cpc_to_cpm(self):
        self.ad_group.settings.update_unsafe(None, cpc=decimal.Decimal("0.1"), cpm=decimal.Decimal("1.0"))

        self._add_sources_with_modifiers(self.input_bid_modifiers_list)

        send_task_patcher = mock.patch("utils.k1_helper._send_task")
        write_history_patcher = mock.patch.object(models.AdGroup, "write_history")

        mock_send_task = send_task_patcher.start()
        mock_write_history = write_history_patcher.start()

        self.ad_group.update_bidding_type(self.request, bidding_type=constants.BiddingType.CPM)

        send_task_patcher.stop()
        write_history_patcher.stop()

        self._assert_ad_group_bid_values(cpc=decimal.Decimal("0.1"), cpm=decimal.Decimal("1.0"))
        self._assert_bid_modifiers(self.input_bid_modifiers_list)
        self._assert_source_bid_values(constants.BiddingType.CPC, [decimal.Decimal("0.03"), decimal.Decimal("0.14")])
        self._assert_source_bid_values(constants.BiddingType.CPM, [decimal.Decimal("0.3"), decimal.Decimal("1.4")])

        self.assertEqual(mock_send_task.call_count, 0)
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

        self.ad_group.update_bidding_type(self.request, bidding_type=constants.BiddingType.CPC)

        send_task_patcher.stop()
        write_history_patcher.stop()

        self._assert_ad_group_bid_values(cpc=decimal.Decimal("0.1"), cpm=decimal.Decimal("1.0"))
        self._assert_bid_modifiers(self.input_bid_modifiers_list)
        self._assert_source_bid_values(constants.BiddingType.CPC, [decimal.Decimal("0.03"), decimal.Decimal("0.14")])
        self._assert_source_bid_values(constants.BiddingType.CPM, [decimal.Decimal("0.3"), decimal.Decimal("1.4")])

        self.assertEqual(mock_send_task.call_count, 0)
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
            target=bid_modifiers.TargetConverter._to_source_target(self.source_1.bidder_slug),
        )

        self.bm_1_2 = magic_mixer.blend(
            models.BidModifier,
            ad_group=self.ad_group_1,
            type=bid_modifiers.BidModifierType.SOURCE,
            modifier=1.0,
            target=bid_modifiers.TargetConverter._to_source_target(self.source_2.bidder_slug),
        )

        self.ad_group_1.settings.update(None, cpc=decimal.Decimal("1.0"))

    def test_ad_group_cpc_over_limit(self):
        self.ad_group_1.settings.update(None, cpc=decimal.Decimal("12.0"))
        self.ad_group_source_1_1.refresh_from_db()
        self.ad_group_source_1_2.refresh_from_db()
        # no validation error, should be handled by blocker
        self.assertEqual(self.ad_group_source_1_1.settings.cpc_cc, decimal.Decimal("12.0"))
        self.assertEqual(self.ad_group_source_1_2.settings.cpc_cc, decimal.Decimal("12.0"))

    def test_ad_group_cpc_under_limit(self):
        self.ad_group_1.settings.update(None, cpc=decimal.Decimal("0.01"))
        self.ad_group_source_1_1.refresh_from_db()
        self.ad_group_source_1_2.refresh_from_db()
        # no validation error, should be handled by blocker
        self.assertEqual(self.ad_group_source_1_1.settings.cpc_cc, decimal.Decimal("0.01"))
        self.assertEqual(self.ad_group_source_1_2.settings.cpc_cc, decimal.Decimal("0.01"))

    def test_ad_group_cpm_over_limit(self):
        self.ad_group_1.update_bidding_type(None, bidding_type=constants.BiddingType.CPM)
        self.ad_group_1.settings.update(None, cpm=decimal.Decimal("12.0"))
        self.ad_group_source_1_1.refresh_from_db()
        self.ad_group_source_1_2.refresh_from_db()
        # no validation error, should be handled by blocker
        self.assertEqual(self.ad_group_source_1_1.settings.cpm, decimal.Decimal("12.0"))
        self.assertEqual(self.ad_group_source_1_2.settings.cpm, decimal.Decimal("12.0"))

    def test_ad_group_cpm_under_limit(self):
        self.ad_group_1.update_bidding_type(None, bidding_type=constants.BiddingType.CPM)
        self.ad_group_1.settings.update(None, cpm=decimal.Decimal("0.01"))
        self.ad_group_source_1_1.refresh_from_db()
        self.ad_group_source_1_2.refresh_from_db()
        # no validation error, should be handled by blocker
        self.assertEqual(self.ad_group_source_1_1.settings.cpm, decimal.Decimal("0.01"))
        self.assertEqual(self.ad_group_source_1_2.settings.cpm, decimal.Decimal("0.01"))

    def test_ad_group_source_cpc_over_limit(self):
        with self.assertRaises(ags_exceptions.MaximalCPCTooHigh):
            self.ad_group_source_1_1.settings.update(None, cpc_cc=decimal.Decimal("12.0"))

    def test_ad_group_source_cpc_under_limit(self):
        with self.assertRaises(ags_exceptions.MinimalCPCTooLow):
            self.ad_group_source_1_1.settings.update(None, cpc_cc=decimal.Decimal("0.01"))

    def test_ad_group_source_cpm_over_limit(self):
        self.ad_group_1.update_bidding_type(None, bidding_type=constants.BiddingType.CPM)
        with self.assertRaises(ags_exceptions.MaximalCPMTooHigh):
            self.ad_group_source_1_1.settings.update(None, cpm=decimal.Decimal("12.0"))

    def test_ad_group_source_cpm_under_limit(self):
        self.ad_group_1.update_bidding_type(None, bidding_type=constants.BiddingType.CPM)
        with self.assertRaises(ags_exceptions.MinimalCPMTooLow):
            self.ad_group_source_1_1.settings.update(None, cpm=decimal.Decimal("0.01"))

    def test_ad_group_source_cpc_over_limit_via_bid_modifier(self):
        with self.assertRaises(ags_exceptions.MaximalCPCTooHigh):
            bid_modifiers.service.set(
                self.ad_group_1,
                bid_modifiers.BidModifierType.SOURCE,
                bid_modifiers.TargetConverter._to_source_target(self.source_1.bidder_slug),
                None,
                10.5,
            )

    def test_ad_group_source_cpc_under_limit_via_bid_modifier(self):
        with self.assertRaises(ags_exceptions.MinimalCPCTooLow):
            bid_modifiers.service.set(
                self.ad_group_1,
                bid_modifiers.BidModifierType.SOURCE,
                bid_modifiers.TargetConverter._to_source_target(self.source_1.bidder_slug),
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

    @mock.patch("automation.autopilot.recalculate_budgets_ad_group")
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
        self.assertEqual(self.ad_group_source.settings.cpc_cc, decimal.Decimal("1.5"))
        self.assertTrue(
            decimal_helpers.equal_decimals(
                self.ad_group.bidmodifier_set.get(
                    type=bid_modifiers.BidModifierType.SOURCE, target=str(self.source.id)
                ).modifier,
                decimal.Decimal("1.5") / decimal.Decimal("4.5"),
            )
        )

    @mock.patch("core.models.settings.ad_group_settings.helpers._replace_with_b1_sources_group_bid_if_needed")
    @mock.patch("automation.autopilot.recalculate_budgets_ad_group")
    def test_create_and_update_ad_group_no_change_on_source(self, mock_autopilot, mock_replace):
        mock_replace.return_value = decimal.Decimal("0.15")

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
        self.assertEqual(self.ad_group_source.settings.cpc_cc, decimal.Decimal("0.15"))
        self.assertTrue(
            decimal_helpers.equal_decimals(
                self.ad_group.bidmodifier_set.get(
                    type=bid_modifiers.BidModifierType.SOURCE, target=str(self.source.id)
                ).modifier,
                decimal.Decimal("0.15") / decimal.Decimal("4.5"),
            )
        )

    @mock.patch("automation.autopilot.recalculate_budgets_ad_group")
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
        self.assertTrue(
            decimal_helpers.equal_decimals(
                self.ad_group.bidmodifier_set.get(
                    type=bid_modifiers.BidModifierType.SOURCE, target=str(self.source.id)
                ).modifier,
                decimal.Decimal("5.0") / decimal.Decimal("5.0"),
            )
        )

    @mock.patch("automation.autopilot.recalculate_budgets_ad_group")
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
        self.assertTrue(
            decimal_helpers.equal_decimals(
                self.ad_group.bidmodifier_set.get(
                    type=bid_modifiers.BidModifierType.SOURCE, target=str(self.source.id)
                ).modifier,
                decimal.Decimal("15.0") / decimal.Decimal("15.0"),
            )
        )


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

        self.assertEqual(self.ad_group_source_1.settings.cpc_cc, decimal.Decimal("1.2000"))
        self.assertEqual(self.ad_group_source_2.settings.cpc_cc, decimal.Decimal("1.2000"))

        self.assertTrue(self._bid_modifier_qs(self.ad_group_source_1).exists())
        self.assertTrue(self._bid_modifier_qs(self.ad_group_source_2).exists())

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


class MirrorOldAndNewBidValuesTestCase(TestCase):
    def setUp(self):
        magic_mixer.blend(
            models.CurrencyExchangeRate,
            currency=constants.Currency.EUR,
            date=dates_helper.local_today(),
            exchange_rate=decimal.Decimal("0.8968"),
        )

        self.ad_group = magic_mixer.blend(
            models.AdGroup, campaign__account__currency=constants.Currency.EUR, bidding_type=constants.BiddingType.CPC
        )
        self.ad_group.settings.update_unsafe(None, autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE)

    def _initial_bid_values(self):
        return {
            "cpc_cc": decimal.Decimal("10.0000"),
            "local_cpc_cc": decimal.Decimal("8.9680"),
            "max_cpm": decimal.Decimal("12.5000"),
            "local_max_cpm": decimal.Decimal("11.2100"),
            "cpc": decimal.Decimal("10.0000"),
            "local_cpc": decimal.Decimal("8.9680"),
            "cpm": decimal.Decimal("12.5000"),
            "local_cpm": decimal.Decimal("11.2100"),
        }

    def _assert_bid_values(self, kwargs):
        for k, v in kwargs.items():
            self.assertEqual(
                getattr(self.ad_group.settings, k),
                v,
                "{}: expected {}, got {}".format(k, v, getattr(self.ad_group.settings, k)),
            )

    def test_change_old_cpc_value(self):
        bid_values = self._initial_bid_values()
        self.ad_group.settings.update_unsafe(None, **bid_values)

        self._assert_bid_values(bid_values)

        self.ad_group.settings.update(None, cpc_cc=decimal.Decimal("15.0000"))

        bid_values.update(
            {
                "cpc_cc": decimal.Decimal("15.0000"),
                "local_cpc_cc": decimal.Decimal("13.4520"),
                "cpc": decimal.Decimal("15.0000"),
                "local_cpc": decimal.Decimal("13.4520"),
            }
        )

        self._assert_bid_values(bid_values)

    def test_change_old_local_cpc_value(self):
        bid_values = self._initial_bid_values()
        self.ad_group.settings.update_unsafe(None, **bid_values)

        self._assert_bid_values(bid_values)

        self.ad_group.settings.update(None, local_cpc_cc=decimal.Decimal("13.4520"))

        bid_values.update(
            {
                "cpc_cc": decimal.Decimal("15.0000"),
                "local_cpc_cc": decimal.Decimal("13.4520"),
                "cpc": decimal.Decimal("15.0000"),
                "local_cpc": decimal.Decimal("13.4520"),
            }
        )

        self._assert_bid_values(bid_values)

    def test_change_new_cpc_value(self):
        bid_values = self._initial_bid_values()
        self.ad_group.settings.update_unsafe(None, **bid_values)

        self._assert_bid_values(bid_values)

        self.ad_group.settings.update(None, cpc=decimal.Decimal("15.0000"))

        bid_values.update(
            {
                "cpc_cc": decimal.Decimal("15.0000"),
                "local_cpc_cc": decimal.Decimal("13.4520"),
                "cpc": decimal.Decimal("15.0000"),
                "local_cpc": decimal.Decimal("13.4520"),
            }
        )

        self._assert_bid_values(bid_values)

    def test_change_new_local_cpc_value(self):
        bid_values = self._initial_bid_values()
        self.ad_group.settings.update_unsafe(None, **bid_values)

        self._assert_bid_values(bid_values)

        self.ad_group.settings.update(None, local_cpc=decimal.Decimal("13.4520"))

        bid_values.update(
            {
                "cpc_cc": decimal.Decimal("15.0000"),
                "local_cpc_cc": decimal.Decimal("13.4520"),
                "cpc": decimal.Decimal("15.0000"),
                "local_cpc": decimal.Decimal("13.4520"),
            }
        )

        self._assert_bid_values(bid_values)

    def test_change_old_cpm_value(self):
        models.AdGroup.objects.filter(id=self.ad_group.id).update(bidding_type=constants.BiddingType.CPM)
        self.ad_group.refresh_from_db()
        bid_values = self._initial_bid_values()
        self.ad_group.settings.update_unsafe(None, **bid_values)

        self._assert_bid_values(bid_values)

        self.ad_group.settings.update(None, max_cpm=decimal.Decimal("15.0000"))

        bid_values.update(
            {
                "max_cpm": decimal.Decimal("15.0000"),
                "local_max_cpm": decimal.Decimal("13.4520"),
                "cpm": decimal.Decimal("15.0000"),
                "local_cpm": decimal.Decimal("13.4520"),
            }
        )

        self._assert_bid_values(bid_values)

    def test_change_old_local_cpm_value(self):
        models.AdGroup.objects.filter(id=self.ad_group.id).update(bidding_type=constants.BiddingType.CPM)
        self.ad_group.refresh_from_db()
        bid_values = self._initial_bid_values()
        self.ad_group.settings.update_unsafe(None, **bid_values)

        self._assert_bid_values(bid_values)

        self.ad_group.settings.update(None, local_max_cpm=decimal.Decimal("13.4520"))

        bid_values.update(
            {
                "max_cpm": decimal.Decimal("15.0000"),
                "local_max_cpm": decimal.Decimal("13.4520"),
                "cpm": decimal.Decimal("15.0000"),
                "local_cpm": decimal.Decimal("13.4520"),
            }
        )

        self._assert_bid_values(bid_values)

    def test_change_new_cpm_value(self):
        models.AdGroup.objects.filter(id=self.ad_group.id).update(bidding_type=constants.BiddingType.CPM)
        self.ad_group.refresh_from_db()
        bid_values = self._initial_bid_values()
        self.ad_group.settings.update_unsafe(None, **bid_values)

        self._assert_bid_values(bid_values)

        self.ad_group.settings.update(None, cpm=decimal.Decimal("15.0000"))

        bid_values.update(
            {
                "max_cpm": decimal.Decimal("15.0000"),
                "local_max_cpm": decimal.Decimal("13.4520"),
                "cpm": decimal.Decimal("15.0000"),
                "local_cpm": decimal.Decimal("13.4520"),
            }
        )

        self._assert_bid_values(bid_values)

    def test_change_new_local_cpm_value(self):
        models.AdGroup.objects.filter(id=self.ad_group.id).update(bidding_type=constants.BiddingType.CPM)
        self.ad_group.refresh_from_db()
        bid_values = self._initial_bid_values()
        self.ad_group.settings.update_unsafe(None, **bid_values)

        self._assert_bid_values(bid_values)

        self.ad_group.settings.update(None, local_cpm=decimal.Decimal("13.4520"))

        bid_values.update(
            {
                "max_cpm": decimal.Decimal("15.0000"),
                "local_max_cpm": decimal.Decimal("13.4520"),
                "cpm": decimal.Decimal("15.0000"),
                "local_cpm": decimal.Decimal("13.4520"),
            }
        )

        self._assert_bid_values(bid_values)

    def test_change_new_cpc_value_unlimited(self):
        bid_values = self._initial_bid_values()
        bid_values.update({"cpc_cc": None, "local_cpc_cc": None, "max_cpm": None, "local_max_cpm": None})
        self.ad_group.settings.update_unsafe(None, **bid_values)

        self._assert_bid_values(bid_values)

        self.ad_group.settings.update(None, cpc=decimal.Decimal("15.0000"))

        bid_values.update(
            {
                "cpc_cc": decimal.Decimal("15.0000"),
                "local_cpc_cc": decimal.Decimal("13.4520"),
                "cpc": decimal.Decimal("15.0000"),
                "local_cpc": decimal.Decimal("13.4520"),
                "max_cpm": decimal.Decimal("12.5000"),
                "local_max_cpm": decimal.Decimal("11.2100"),
            }
        )

        self._assert_bid_values(bid_values)

    def test_change_new_local_cpc_value_unlimited(self):
        bid_values = self._initial_bid_values()
        bid_values.update({"cpc_cc": None, "local_cpc_cc": None, "max_cpm": None, "local_max_cpm": None})
        self.ad_group.settings.update_unsafe(None, **bid_values)

        self._assert_bid_values(bid_values)

        self.ad_group.settings.update(None, local_cpc=decimal.Decimal("13.4520"))

        bid_values.update(
            {
                "cpc_cc": decimal.Decimal("15.0000"),
                "local_cpc_cc": decimal.Decimal("13.4520"),
                "cpc": decimal.Decimal("15.0000"),
                "local_cpc": decimal.Decimal("13.4520"),
                "max_cpm": decimal.Decimal("12.5000"),
                "local_max_cpm": decimal.Decimal("11.2100"),
            }
        )

        self._assert_bid_values(bid_values)


@mock.patch("automation.autopilot.recalculate_budgets_ad_group", mock.MagicMock())
@mock.patch.object(core.features.multicurrency, "get_current_exchange_rate")
class MirrorOldBidValuesOnCreateTest(TestCase):
    def setUp(self):
        self.request = magic_mixer.blend_request_user(permissions=["fea_can_use_cpm_buying"])
        self.campaign = magic_mixer.blend(models.Campaign)
        self.exchange_rate = decimal.Decimal("2.0")
        self.max_autopilot_bid = decimal.Decimal("5.0")

    def test_cpc_inactive_autopilot(self, mock_get_exchange_rate):
        mock_get_exchange_rate.return_value = self.exchange_rate
        ad_group = models.AdGroup.objects.create(
            self.request,
            self.campaign,
            bidding_type=constants.BiddingType.CPC,
            initial_settings={
                "autopilot_state": constants.AdGroupSettingsAutopilotState.INACTIVE,
                "max_autopilot_bid": self.max_autopilot_bid,
            },
        )

        self.assertEqual(ad_group.settings.cpc, models.AdGroupSettings.DEFAULT_CPC_VALUE)
        self.assertEqual(ad_group.settings.local_cpc, models.AdGroupSettings.DEFAULT_CPC_VALUE * self.exchange_rate)
        self.assertEqual(ad_group.settings.cpc_cc, models.AdGroupSettings.DEFAULT_CPC_VALUE)
        self.assertEqual(ad_group.settings.local_cpc_cc, models.AdGroupSettings.DEFAULT_CPC_VALUE * self.exchange_rate)
        self.assertEqual(ad_group.settings.cpm, models.AdGroupSettings.DEFAULT_CPM_VALUE)
        self.assertEqual(ad_group.settings.local_cpm, models.AdGroupSettings.DEFAULT_CPM_VALUE * self.exchange_rate)
        self.assertEqual(ad_group.settings.max_cpm, models.AdGroupSettings.DEFAULT_CPM_VALUE)
        self.assertEqual(ad_group.settings.local_max_cpm, models.AdGroupSettings.DEFAULT_CPM_VALUE * self.exchange_rate)

    def test_cpc_active_autopilot(self, mock_get_exchange_rate):
        mock_get_exchange_rate.return_value = self.exchange_rate
        ad_group = models.AdGroup.objects.create(
            self.request,
            self.campaign,
            bidding_type=constants.BiddingType.CPC,
            initial_settings={
                "autopilot_state": constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,
                "max_autopilot_bid": self.max_autopilot_bid,
            },
        )

        self.assertEqual(ad_group.settings.cpc, models.AdGroupSettings.DEFAULT_CPC_VALUE)
        self.assertEqual(ad_group.settings.local_cpc, models.AdGroupSettings.DEFAULT_CPC_VALUE * self.exchange_rate)
        self.assertEqual(ad_group.settings.cpc_cc, self.max_autopilot_bid)
        self.assertEqual(ad_group.settings.local_cpc_cc, self.max_autopilot_bid * self.exchange_rate)
        self.assertEqual(ad_group.settings.cpm, models.AdGroupSettings.DEFAULT_CPM_VALUE)
        self.assertEqual(ad_group.settings.local_cpm, models.AdGroupSettings.DEFAULT_CPM_VALUE * self.exchange_rate)
        self.assertEqual(ad_group.settings.max_cpm, None)
        self.assertEqual(ad_group.settings.local_max_cpm, None)

    def test_cpm_inactive_autopilot(self, mock_get_exchange_rate):
        mock_get_exchange_rate.return_value = self.exchange_rate
        ad_group = models.AdGroup.objects.create(
            self.request,
            self.campaign,
            bidding_type=constants.BiddingType.CPM,
            initial_settings={
                "autopilot_state": constants.AdGroupSettingsAutopilotState.INACTIVE,
                "max_autopilot_bid": self.max_autopilot_bid,
            },
        )

        self.assertEqual(ad_group.settings.cpc, models.AdGroupSettings.DEFAULT_CPC_VALUE)
        self.assertEqual(ad_group.settings.local_cpc, models.AdGroupSettings.DEFAULT_CPC_VALUE * self.exchange_rate)
        self.assertEqual(ad_group.settings.cpc_cc, models.AdGroupSettings.DEFAULT_CPC_VALUE)
        self.assertEqual(ad_group.settings.local_cpc_cc, models.AdGroupSettings.DEFAULT_CPC_VALUE * self.exchange_rate)
        self.assertEqual(ad_group.settings.cpm, models.AdGroupSettings.DEFAULT_CPM_VALUE)
        self.assertEqual(ad_group.settings.local_cpm, models.AdGroupSettings.DEFAULT_CPM_VALUE * self.exchange_rate)
        self.assertEqual(ad_group.settings.max_cpm, models.AdGroupSettings.DEFAULT_CPM_VALUE)
        self.assertEqual(ad_group.settings.local_max_cpm, models.AdGroupSettings.DEFAULT_CPM_VALUE * self.exchange_rate)

    def test_cpm_active_autopilot(self, mock_get_exchange_rate):
        mock_get_exchange_rate.return_value = self.exchange_rate
        ad_group = models.AdGroup.objects.create(
            self.request,
            self.campaign,
            bidding_type=constants.BiddingType.CPM,
            initial_settings={
                "autopilot_state": constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,
                "max_autopilot_bid": self.max_autopilot_bid,
            },
        )

        self.assertEqual(ad_group.settings.cpc, models.AdGroupSettings.DEFAULT_CPC_VALUE)
        self.assertEqual(ad_group.settings.local_cpc, models.AdGroupSettings.DEFAULT_CPC_VALUE * self.exchange_rate)
        self.assertEqual(ad_group.settings.cpc_cc, None)
        self.assertEqual(ad_group.settings.local_cpc_cc, None)
        self.assertEqual(ad_group.settings.cpm, models.AdGroupSettings.DEFAULT_CPM_VALUE)
        self.assertEqual(ad_group.settings.local_cpm, models.AdGroupSettings.DEFAULT_CPM_VALUE * self.exchange_rate)
        self.assertEqual(ad_group.settings.max_cpm, self.max_autopilot_bid)
        self.assertEqual(ad_group.settings.local_max_cpm, self.max_autopilot_bid * self.exchange_rate)


class AllRTBUpdateTestCase(TestCase):
    def setUp(self):
        magic_mixer.blend(
            models.CurrencyExchangeRate,
            currency=constants.Currency.EUR,
            date=dates_helper.local_today(),
            exchange_rate=decimal.Decimal("0.8968"),
        )

        self.ad_group = magic_mixer.blend(
            models.AdGroup, bidding_type=constants.BiddingType.CPC, campaign__account__currency=constants.Currency.EUR
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

    def _initial_ad_group_settings(self):
        return {
            "cpc_cc": None,
            "local_cpc_cc": None,
            "max_cpm": None,
            "local_max_cpm": None,
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

    def _initial_ad_group_source_settings(self):
        return {
            "cpc_cc": decimal.Decimal("0.2230"),
            "local_cpc_cc": decimal.Decimal("0.2000"),
            "cpm": decimal.Decimal("0.9852"),
            "local_cpm": decimal.Decimal("0.8835"),
        }

    def _assert_ad_group_state(self, settings):
        for k, v in settings.items():
            self.assertEqual(
                getattr(self.ad_group.settings, k),
                v,
                "{}: expected {}, got {}".format(k, v, getattr(self.ad_group.settings, k)),
            )

    def _assert_ad_group_source_state(self, ad_group_source, settings, bid_modifier_value):
        for k, v in settings.items():
            self.assertEqual(
                getattr(ad_group_source.settings, k),
                v,
                "{}: expected {}, got {}".format(k, v, getattr(ad_group_source.settings, k)),
            )

        self.assertAlmostEqual(
            self.ad_group.bidmodifier_set.get(
                type=bid_modifiers.BidModifierType.SOURCE, target=str(ad_group_source.source.id)
            ).modifier,
            bid_modifier_value,
            places=8,
        )

    def test_autopilot_b1_sources_group_update(self):
        ad_group_settings = self._initial_ad_group_settings()
        ad_group_settings.update({"autopilot_state": constants.AdGroupSettingsAutopilotState.ACTIVE_CPC})
        ad_group_source_settings = self._initial_ad_group_source_settings()
        self._setup_ad_group_and_sources(ad_group_settings, ad_group_source_settings, ad_group_source_settings)

        autopilot_helpers.update_ad_group_b1_sources_group_values(self.ad_group, {"cpc_cc": decimal.Decimal("0.4000")})

        self.ad_group.refresh_from_db()
        self.ad_group_source_1.refresh_from_db()
        self.ad_group_source_2.refresh_from_db()

        self._assert_ad_group_state(
            {
                "cpc": decimal.Decimal("20.0000"),
                "local_cpc": decimal.Decimal("17.9360"),
                "b1_sources_group_cpc_cc": decimal.Decimal("0.4000"),
                "local_b1_sources_group_cpc_cc": decimal.Decimal("0.3587"),
            }
        )

        self._assert_ad_group_source_state(
            self.ad_group_source_1,
            {"cpc_cc": decimal.Decimal("0.2230"), "local_cpc_cc": decimal.Decimal("0.2000")},
            float(decimal.Decimal("0.2230") / decimal.Decimal("20.0000")),
        )

        self._assert_ad_group_source_state(
            self.ad_group_source_2,
            {"cpc_cc": decimal.Decimal("0.4000"), "local_cpc_cc": decimal.Decimal("0.3587")},
            float(decimal.Decimal("0.4000") / decimal.Decimal("20.0000")),
        )

    def test_manual_b1_sources_group_update(self):
        # manual setting of b1 sources group value is disabled in dashboard, but is still available through API
        ad_group_settings = self._initial_ad_group_settings()
        ad_group_settings.update({"autopilot_state": constants.AdGroupSettingsAutopilotState.INACTIVE})
        ad_group_source_settings = self._initial_ad_group_source_settings()
        self._setup_ad_group_and_sources(ad_group_settings, ad_group_source_settings, ad_group_source_settings)

        self.ad_group.settings.update(None, b1_sources_group_cpc_cc=decimal.Decimal("0.4000"))

        self.ad_group.refresh_from_db()
        self.ad_group_source_1.refresh_from_db()
        self.ad_group_source_2.refresh_from_db()

        self._assert_ad_group_state(
            {
                "cpc": decimal.Decimal("20.0000"),
                "local_cpc": decimal.Decimal("17.9360"),
                "b1_sources_group_cpc_cc": decimal.Decimal("0.4000"),
                "local_b1_sources_group_cpc_cc": decimal.Decimal("0.3587"),
            }
        )

        self._assert_ad_group_source_state(
            self.ad_group_source_1,
            {"cpc_cc": decimal.Decimal("0.2230"), "local_cpc_cc": decimal.Decimal("0.2000")},
            float(decimal.Decimal("0.2230") / decimal.Decimal("20.0000")),
        )

        self._assert_ad_group_source_state(
            self.ad_group_source_2,
            {"cpc_cc": decimal.Decimal("0.4000"), "local_cpc_cc": decimal.Decimal("0.3587")},
            float(decimal.Decimal("0.4000") / decimal.Decimal("20.0000")),
        )

    def test_manual_ad_group_cpc_update(self):
        ad_group_settings = self._initial_ad_group_settings()
        ad_group_settings.update({"autopilot_state": constants.AdGroupSettingsAutopilotState.INACTIVE})
        ad_group_source_settings = self._initial_ad_group_source_settings()
        self._setup_ad_group_and_sources(ad_group_settings, ad_group_source_settings, ad_group_source_settings)

        self.ad_group.settings.update(None, cpc=decimal.Decimal("15.0000"))

        self.ad_group.refresh_from_db()
        self.ad_group_source_1.refresh_from_db()
        self.ad_group_source_2.refresh_from_db()

        self._assert_ad_group_state(
            {
                "cpc": decimal.Decimal("15.0000"),
                "local_cpc": decimal.Decimal("13.4520"),
                "b1_sources_group_cpc_cc": decimal.Decimal("0.2230"),
                "local_b1_sources_group_cpc_cc": decimal.Decimal("0.2000"),
            }
        )

        self._assert_ad_group_source_state(
            self.ad_group_source_1,
            {"cpc_cc": decimal.Decimal("0.1673"), "local_cpc_cc": decimal.Decimal("0.1500")},
            float(decimal.Decimal("0.1673") / decimal.Decimal("15.0000")),
        )

        self._assert_ad_group_source_state(
            self.ad_group_source_2,
            {"cpc_cc": decimal.Decimal("0.1673"), "local_cpc_cc": decimal.Decimal("0.1500")},
            float(decimal.Decimal("0.1673") / decimal.Decimal("15.0000")),
        )


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

        ad_group.settings.update_unsafe(
            None,
            cpc_cc=None,
            local_cpc_cc=None,
            max_cpm=None,
            local_max_cpm=None,
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
            cpc_cc=None,
            local_cpc_cc=None,
            max_cpm=None,
            local_max_cpm=None,
            cpc=decimal.Decimal("20.0000"),
            local_cpc=decimal.Decimal("17.9360"),
            cpm=decimal.Decimal("25.0000"),
            local_cpm=decimal.Decimal("22.4200"),
            autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE,
        )

        ad_group_2.settings.update_unsafe(
            None,
            cpc_cc=decimal.Decimal("10.0000"),
            local_cpc_cc=decimal.Decimal("8.9680"),
            max_cpm=decimal.Decimal("12.5000"),
            local_max_cpm=decimal.Decimal("11.2100"),
            cpc=decimal.Decimal("10.0000"),
            local_cpc=decimal.Decimal("8.9680"),
            cpm=decimal.Decimal("12.5000"),
            local_cpm=decimal.Decimal("11.2100"),
            autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE,
        )

        self.assertEqual(ad_group_1.settings.cpc_cc, None)
        self.assertEqual(ad_group_1.settings.local_cpc_cc, None)
        self.assertEqual(ad_group_1.settings.max_cpm, None)
        self.assertEqual(ad_group_1.settings.local_max_cpm, None)
        self.assertEqual(ad_group_1.settings.cpc, decimal.Decimal("20.0000"))
        self.assertEqual(ad_group_1.settings.local_cpc, decimal.Decimal("17.9360"))
        self.assertEqual(ad_group_1.settings.cpm, decimal.Decimal("25.0000"))
        self.assertEqual(ad_group_1.settings.local_cpm, decimal.Decimal("22.4200"))

        self.assertEqual(ad_group_2.settings.cpc_cc, decimal.Decimal("10.0000"))
        self.assertEqual(ad_group_2.settings.local_cpc_cc, decimal.Decimal("8.9680"))
        self.assertEqual(ad_group_2.settings.max_cpm, decimal.Decimal("12.5000"))
        self.assertEqual(ad_group_2.settings.local_max_cpm, decimal.Decimal("11.2100"))
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

        self.assertEqual(ad_group_1.settings.cpc_cc, decimal.Decimal("19.7947"))
        self.assertEqual(ad_group_1.settings.local_cpc_cc, decimal.Decimal("17.9360"))
        self.assertEqual(ad_group_1.settings.max_cpm, decimal.Decimal("24.7434"))
        self.assertEqual(ad_group_1.settings.local_max_cpm, decimal.Decimal("22.4200"))
        self.assertEqual(ad_group_1.settings.cpc, decimal.Decimal("19.7947"))
        self.assertEqual(ad_group_1.settings.local_cpc, decimal.Decimal("17.9360"))
        self.assertEqual(ad_group_1.settings.cpm, decimal.Decimal("24.7434"))
        self.assertEqual(ad_group_1.settings.local_cpm, decimal.Decimal("22.4200"))

        self.assertEqual(ad_group_2.settings.cpc_cc, decimal.Decimal("9.8974"))
        self.assertEqual(ad_group_2.settings.local_cpc_cc, decimal.Decimal("8.9680"))
        self.assertEqual(ad_group_2.settings.max_cpm, decimal.Decimal("12.3717"))
        self.assertEqual(ad_group_2.settings.local_max_cpm, decimal.Decimal("11.2100"))
        self.assertEqual(ad_group_2.settings.cpc, decimal.Decimal("9.8974"))
        self.assertEqual(ad_group_2.settings.local_cpc, decimal.Decimal("8.9680"))
        self.assertEqual(ad_group_2.settings.cpm, decimal.Decimal("12.3717"))
        self.assertEqual(ad_group_2.settings.local_cpm, decimal.Decimal("11.2100"))


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

        self.request = magic_mixer.blend_request_user(["fea_can_use_cpm_buying"])

    @mock.patch("automation.autopilot.recalculate_budgets_ad_group")
    def test_cpc(self, mock_autopilot):
        self.ad_group = models.AdGroup.objects.create(
            self.request,
            self.campaign,
            bidding_type=constants.BiddingType.CPC,
            initial_settings={
                "autopilot_state": constants.AdGroupSettingsAutopilotState.INACTIVE,
                "cpc": decimal.Decimal("5.0"),
            },
        )

        self.ad_group_source_1 = self.ad_group.adgroupsource_set.get(source=self.source_1)
        self.ad_group_source_2 = self.ad_group.adgroupsource_set.get(source=self.source_2)
        self.assertEqual(self.ad_group_source_1.settings.cpc_cc, decimal.Decimal("5.0"))
        self.assertEqual(self.ad_group_source_2.settings.cpc_cc, decimal.Decimal("5.0"))

        self.ad_group.settings.update(
            None,
            autopilot_state=constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,
            max_autopilot_bid=decimal.Decimal("3.0"),
        )

        self.ad_group_source_1.refresh_from_db()
        self.ad_group_source_2.refresh_from_db()

        self.assertEqual(self.ad_group_source_1.settings.cpc_cc, decimal.Decimal("3.0"))
        self.assertEqual(self.ad_group_source_2.settings.cpc_cc, decimal.Decimal("3.0"))

        self.ad_group.settings.update(
            None, autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE, cpc=decimal.Decimal("20.0")
        )

        self.ad_group_source_1.refresh_from_db()
        self.ad_group_source_2.refresh_from_db()

        self.assertEqual(self.ad_group_source_1.settings.cpc_cc, decimal.Decimal("12.0"))
        self.assertEqual(self.ad_group_source_2.settings.cpc_cc, decimal.Decimal("12.0"))

        self.ad_group.settings.update(
            None,
            autopilot_state=constants.AdGroupSettingsAutopilotState.ACTIVE_CPC,
            max_autopilot_bid=decimal.Decimal("11.0"),
        )

        self.ad_group_source_1.refresh_from_db()
        self.ad_group_source_2.refresh_from_db()

        self.assertEqual(self.ad_group_source_1.settings.cpc_cc, decimal.Decimal("11.0"))
        self.assertEqual(self.ad_group_source_2.settings.cpc_cc, decimal.Decimal("11.0"))

    @mock.patch("automation.autopilot.recalculate_budgets_ad_group")
    def test_cpm(self, mock_autopilot):
        self.ad_group = models.AdGroup.objects.create(
            self.request,
            self.campaign,
            bidding_type=constants.BiddingType.CPM,
            initial_settings={
                "autopilot_state": constants.AdGroupSettingsAutopilotState.INACTIVE,
                "cpm": decimal.Decimal("5.0"),
            },
        )

        self.ad_group_source_1 = self.ad_group.adgroupsource_set.get(source=self.source_1)
        self.ad_group_source_2 = self.ad_group.adgroupsource_set.get(source=self.source_2)
        self.assertEqual(self.ad_group_source_1.settings.cpm, decimal.Decimal("5.0"))
        self.assertEqual(self.ad_group_source_2.settings.cpm, decimal.Decimal("5.0"))

        self.ad_group.settings.update(
            None,
            autopilot_state=constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,
            max_autopilot_bid=decimal.Decimal("3.0"),
        )

        self.ad_group_source_1.refresh_from_db()
        self.ad_group_source_2.refresh_from_db()

        self.assertEqual(self.ad_group_source_1.settings.cpm, decimal.Decimal("3.0"))
        self.assertEqual(self.ad_group_source_2.settings.cpm, decimal.Decimal("3.0"))

        self.ad_group.settings.update(
            None, autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE, cpm=decimal.Decimal("20.0")
        )

        self.ad_group_source_1.refresh_from_db()
        self.ad_group_source_2.refresh_from_db()

        self.assertEqual(self.ad_group_source_1.settings.cpm, decimal.Decimal("12.0"))
        self.assertEqual(self.ad_group_source_2.settings.cpm, decimal.Decimal("12.0"))

        self.ad_group.settings.update(
            None,
            autopilot_state=constants.AdGroupSettingsAutopilotState.ACTIVE_CPC,
            max_autopilot_bid=decimal.Decimal("11.0"),
        )

        self.ad_group_source_1.refresh_from_db()
        self.ad_group_source_2.refresh_from_db()

        self.assertEqual(self.ad_group_source_1.settings.cpm, decimal.Decimal("11.0"))
        self.assertEqual(self.ad_group_source_2.settings.cpm, decimal.Decimal("11.0"))
