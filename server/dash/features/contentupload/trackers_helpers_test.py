from django.test import TestCase

from dash import constants

from . import trackers_helpers


class TrackersHelpersTest(TestCase):
    def test_convert_legacy_trackers(self):
        tracker_urls = [
            "https://www.example.com/pixel.png?gdpr=${gdpr}&gdpr_consent=${gdpr_consent_50}&us_privacy=${us_privacy}",
            "https://www.example.com/pixel2.png",
        ]
        trackers = trackers_helpers.convert_legacy_trackers(tracker_urls, tracker_optional=True)
        self.assertEqual(
            trackers,
            [
                {
                    "event_type": constants.TrackerEventType.IMPRESSION,
                    "method": constants.TrackerMethod.IMG,
                    "url": "https://www.example.com/pixel.png?gdpr=${gdpr}&gdpr_consent=${gdpr_consent_50}&us_privacy=${us_privacy}",
                    "fallback_url": None,
                    "supported_privacy_frameworks": [
                        constants.TrackerPrivacyFramework.GDPR,
                        constants.TrackerPrivacyFramework.CCPA,
                    ],
                    "tracker_optional": True,
                },
                {
                    "event_type": constants.TrackerEventType.IMPRESSION,
                    "method": constants.TrackerMethod.IMG,
                    "url": "https://www.example.com/pixel2.png",
                    "fallback_url": None,
                    "supported_privacy_frameworks": [],
                    "tracker_optional": True,
                },
            ],
        )

    def test_get_tracker(self):
        tracker_url = "https://www.example.com/tracker.js"
        event_type = constants.TrackerEventType.VIEWABILITY
        method = constants.TrackerMethod.JS
        fallback_url = "https://www.example.com/pixel.png"
        tracker_optional = False

        self.assertEqual(
            trackers_helpers.get_tracker(
                url=tracker_url,
                fallback_url=fallback_url,
                event_type=event_type,
                method=method,
                tracker_optional=tracker_optional,
            ),
            {
                "event_type": constants.TrackerEventType.VIEWABILITY,
                "method": constants.TrackerMethod.JS,
                "url": "https://www.example.com/tracker.js",
                "fallback_url": "https://www.example.com/pixel.png",
                "supported_privacy_frameworks": [],
                "tracker_optional": False,
            },
        )

    def test_get_privacy_frameworks(self):
        tracker_url = (
            "https://www.example.com/pixel.png?gdpr=${gdpr}&gdpr_consent=${gdpr_consent_50}&us_privacy=${us_privacy}"
        )
        fallback_url = (
            "https://www.example.com/pixel23.png?gdpr=${gdpr}&gdpr_consent=${gdpr_consent_50}&us_privacy=${us_privacy}"
        )
        privacy_frameworks = trackers_helpers.get_privacy_frameworks(tracker_url, fallback_url)
        self.assertEqual(
            privacy_frameworks, [constants.TrackerPrivacyFramework.GDPR, constants.TrackerPrivacyFramework.CCPA]
        )

        tracker_url = (
            "https://www.example.com/pixel.png?gdpr=${gdpr}&gdpr_consent=${gdpr_consent_50}&us_privacy=${us_privacy}"
        )
        fallback_url = "https://www.example.com/pixel23.png?gdpr=${gdpr}&gdpr_consent=${gdpr_consent_50}"
        privacy_frameworks = trackers_helpers.get_privacy_frameworks(tracker_url, fallback_url)
        self.assertEqual(privacy_frameworks, [constants.TrackerPrivacyFramework.GDPR])

        tracker_url = "https://www.example.com/pixel.png?gdpr=${gdpr}&gdpr_consent=${gdpr_consent_50}"
        fallback_url = (
            "https://www.example.com/pixel23.png?gdpr=${gdpr}&gdpr_consent=${gdpr_consent_50}&us_privacy=${us_privacy}"
        )
        privacy_frameworks = trackers_helpers.get_privacy_frameworks(tracker_url, fallback_url)
        self.assertEqual(privacy_frameworks, [constants.TrackerPrivacyFramework.GDPR])

        tracker_url = "https://www.example.com/pixel.png?gdpr=${gdpr}&gdpr_consent=${gdpr_consent_50}"
        fallback_url = "https://www.example.com/pixel23.png"
        privacy_frameworks = trackers_helpers.get_privacy_frameworks(tracker_url, fallback_url)
        self.assertEqual(privacy_frameworks, [])

        tracker_url = "https://www.example.com/pixel.png?gdpr_consent=${gdpr_consent_50}"
        fallback_url = None
        privacy_frameworks = trackers_helpers.get_privacy_frameworks(tracker_url, fallback_url)
        self.assertEqual(privacy_frameworks, [constants.TrackerPrivacyFramework.GDPR])

        tracker_url = "https://www.example.com/pixel.png?gdpr=${gdpr}"
        fallback_url = "https://www.example.com/pixel.png?gdpr=${gdpr}&gdpr_consent=${gdpr_consent_50}"
        privacy_frameworks = trackers_helpers.get_privacy_frameworks(tracker_url, fallback_url)
        self.assertEqual(privacy_frameworks, [constants.TrackerPrivacyFramework.GDPR])

        tracker_url = "https://www.example.com/pixel.png"
        fallback_url = "https://www.example.com/pixel23.png?gdpr=${gdpr}&gdpr_consent=${gdpr_consent_50}"
        privacy_frameworks = trackers_helpers.get_privacy_frameworks(tracker_url, fallback_url)
        self.assertEqual(privacy_frameworks, [])

        tracker_url = None
        fallback_url = None
        privacy_frameworks = trackers_helpers.get_privacy_frameworks(tracker_url, fallback_url)
        self.assertEqual(privacy_frameworks, [])

        tracker_url = ""
        fallback_url = ""
        privacy_frameworks = trackers_helpers.get_privacy_frameworks(tracker_url, fallback_url)
        self.assertEqual(privacy_frameworks, [])
