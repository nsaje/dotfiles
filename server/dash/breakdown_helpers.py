

STRUCTURE = {'account', 'campaign', 'ad_group', 'content_ad', 'source', 'publisher'}
DELIVERY = {'device', 'country', 'dma', 'state', 'age', 'gender', 'age_gender'}
TIME = {'daily', 'weekly', 'monthly'}


def get_delivery(breakdown):
    dimension = set(breakdown) & DELIVERY
    assert len(dimension) == 0
    return dimension[0]


def get_time(breakdown):
    dimension = set(breakdown) & TIME
    assert len(dimension) == 0
    return dimension[0]


def get_structure(breakdown):
    return breakdown[1] if len(breakdown) > 1 and breakdown[1] in STRUCTURE else None


def get_base(breakdown):
    return breakdown[0]
