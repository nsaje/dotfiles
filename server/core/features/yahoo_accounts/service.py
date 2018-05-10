from . import YahooAccount


DEFAULT_ADVERTISER_ID = '953699'


def get_default_account():
    return YahooAccount.objects.get(advertiser_id=DEFAULT_ADVERTISER_ID)
