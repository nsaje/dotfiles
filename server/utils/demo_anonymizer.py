import itertools

_name_pools = None
_fake_factory = None


class DemoNamePools(object):
    def __init__(self, account_names, campaign_names, ad_group_names):
        self.account_names = itertools.cycle(account_names)
        self.campaign_names = itertools.cycle(campaign_names)
        self.ad_group_names = itertools.cycle(ad_group_names)


def set_name_pools(name_pools):
    global _name_pools
    _name_pools = name_pools


def set_fake_factory(fake_factory):
    global _fake_factory
    _fake_factory = fake_factory


def account_name_from_pool():
    return next(_name_pools.account_names)


def campaign_name_from_pool():
    return next(_name_pools.campaign_names)


def ad_group_name_from_pool():
    return next(_name_pools.ad_group_names)


def fake_email():
    return _fake_factory.email()


def fake_username():
    return _fake_factory.user_name()


def fake_first_name():
    return _fake_factory.first_name()


def fake_last_name():
    return _fake_factory.last_name()


def fake_url():
    return _fake_factory.url()


def fake_content_ad_url():
    return "https://www.example.com/p/" + _fake_factory.uuid4()


def fake_display_url():
    return _fake_factory.domain_name()[-25:].lstrip("-")


def fake_brand():
    return ("%s-%s" % (_fake_factory.last_name(), _fake_factory.last_name()))[:25]


def fake_sentence():
    return _fake_factory.sentence()


def fake_io():
    return "https://s3.amazonaws.com/z1-static/demo/Zemanta+One+-+Acme.pdf"
