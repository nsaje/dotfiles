from django.test import TestCase

from . import formatters


class RuleHistoryFormattersTestCase(TestCase):
    def test_format_bid_modifier(self):
        def get_mapping():
            return {"UK": "United Kingdom"}

        formatter = formatters.get_bid_modifier_formatter("Increased", "for countries", get_mapping)
        self.assertEqual(
            "Increased bid modifier for 0.1% for countries: United Kingdom (0.2%)",
            formatter(0.1, {"UK": {"old_value": 0.1, "new_value": 0.2}}),
        )

    def test_format_paused(self):
        def get_mapping():
            return {43: "triplelift"}

        formatter = formatters.get_paused_formatter("media sources", get_mapping)
        self.assertEqual("Paused media sources: triplelift", formatter(0, {"43": {"old_value": 1, "new_value": 2}}))

    def test_format_bid(self):
        formatter = formatters.get_bid_formatter("Increased", "ad group")
        self.assertEqual(
            "Increased ad group bid for $1 to $2", formatter(1, {"1234": {"old_value": 1, "new_value": 2}})
        )

    def test_format_budget(self):
        formatter = formatters.get_budget_formatter("Increased", "ad group")
        self.assertEqual(
            "Increased ad group daily budget from $1 to $2", formatter(1, {"1234": {"old_value": 1, "new_value": 2}})
        )

    def test_format_email(self):
        formatter = formatters.get_email_formatter("ad group")
        self.assertEqual("Sent ad group email", formatter(0, {"1234": {"old_value": 1, "new_value": 2}}))

    def test_format_blacklist(self):
        def get_mapping():
            return {}

        formatter = formatters.get_blacklist_formatter("publishers", get_mapping)
        self.assertEqual(
            "Blacklisted publishers: www.cnn.com, www.bbc.com",
            formatter(
                0, {"www.cnn.com": {"old_value": 1, "new_value": 2}, "www.bbc.com": {"old_value": 1, "new_value": 2}}
            ),
        )

    def test_format_add_to_publisher(self):
        def get_mapping():
            return {}

        formatter = formatters.get_add_to_publisher_formatter(get_mapping)
        self.assertEqual(
            "Added publisher to the publisher group: www.cnn.com, www.bbc.com",
            formatter(
                0, {"www.cnn.com": {"old_value": 1, "new_value": 2}, "www.bbc.com": {"old_value": 1, "new_value": 2}}
            ),
        )

    def test_get_changes_breakdown(self):
        self.assertEqual([], formatters._get_changes_breakdown({}, {}))
        self.assertEqual(
            ["www.cnn.com", "www.bbc.com"],
            formatters._get_changes_breakdown(
                {"www.cnn.com": {"old_value": 1, "new_value": 2}, "www.bbc.com": {"old_value": 1, "new_value": 2}}, {}
            ),
        )
        self.assertEqual(
            ["1234 (0.2%)"], formatters._get_changes_breakdown({"1234": {"old_value": 0.1, "new_value": 0.2}}, {}, True)
        )

    def test_get_mapped_item(self):
        self.assertEqual("www.cnn.com", formatters._get_mapped_item("www.cnn.com", {}))
        self.assertEqual("iOS", formatters._get_mapped_item("ios", {"ios": "iOS"}))
        self.assertEqual("triplelift", formatters._get_mapped_item("43", {43: "triplelift"}))
