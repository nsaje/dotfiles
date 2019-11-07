from utils.constant_base import ConstantBase

MAX_TITLE_LENGTH = 90
MAX_DESCRIPTION_LENGTH = 150
MAX_DISPLAY_URL_LENGTH = 35
MAX_BRAND_NAME_LENGTH = 25


class FeedTypes(ConstantBase):
    YAHOO_NEWS_RSS = 1
    YAHOO_SPORTS_RSS = 2
    GOOGLE_FEED = 3

    _VALUES = {YAHOO_NEWS_RSS: "Yahoo news feed", YAHOO_SPORTS_RSS: "Yahoo sports feed", GOOGLE_FEED: "Google feed"}


class FeedStatus(ConstantBase):
    ENABLED = 1
    DISABLED = 2

    _VALUES = {ENABLED: "Enabled", DISABLED: "Disabled"}


FEEDS_TAG_MAPPING = {
    FeedTypes.YAHOO_NEWS_RSS: {
        "elements_name": "item",
        "elements_mapping": {"title": "title", "description": "description", "url": "link", "image_url": "content"},
    },
    FeedTypes.YAHOO_SPORTS_RSS: {
        "elements_name": "item",
        "elements_mapping": {"title": "title", "description": "description", "url": "link", "image_url": "encoded"},
    },
    FeedTypes.GOOGLE_FEED: {
        "elements_name": "product",
        "elements_mapping": {
            "title": "title",
            "description": "description",
            "url": "link",
            "image_url": "image_link",
            "brand_name": "brand",
        },
    },
}
