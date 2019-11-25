from utils.constant_base import ConstantBase

MAX_TITLE_LENGTH = 90
MAX_DESCRIPTION_LENGTH = 150
MAX_DISPLAY_URL_LENGTH = 35
MAX_BRAND_NAME_LENGTH = 25

CUSTOM_FLAG_BRAND = "z1_product_feed_brand"


class FeedTypes(ConstantBase):
    YAHOO_NEWS_RSS = 1
    YAHOO_SPORTS_RSS = 2
    GOOGLE_FEED = 3
    REPLY_IT_FEED = 4

    _VALUES = {
        YAHOO_NEWS_RSS: "Yahoo news feed",
        YAHOO_SPORTS_RSS: "Yahoo sports feed",
        GOOGLE_FEED: "Google feed",
        REPLY_IT_FEED: "Reply.it feed",
    }


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
            "display_url": "link",
        },
    },
    FeedTypes.REPLY_IT_FEED: {
        "elements_name": "item",
        "elements_mapping": {
            "title": "title",
            "description": "description",
            "url": "url",
            "image_url": "img",
            "brand_name": "brand_name_friendly",
            "display_url": "displayed_url",
            "primary_tracker_url": "impression_tracker",
            "call_to_action": "cta_text",
        },
    },
}
