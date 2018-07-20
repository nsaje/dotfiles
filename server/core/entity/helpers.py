from django.core.cache import caches

import core.source

NR_OF_DAYS_INACTIVE_FOR_ARCHIVAL = 3  # number of days an ad group is paused before it can be archived.


def generate_parents(ad_group=None, campaign=None, account=None, agency=None):
    """
    For first given entity in order check if it has any parents and return them.
    E.g. given and ad group return also it's campaign, account and agency if any
    """
    campaign = campaign or ad_group and ad_group.campaign
    account = account or campaign and campaign.account
    agency = agency or account and account.agency
    return campaign, account, agency


def should_filter_by_sources(sources):
    if sources is None:
        return False

    cache = caches["local_memory_cache"]
    all_source_ids = cache.get("all_source_ids")
    if not all_source_ids:
        all_source_ids = core.source.Source.objects.all().values_list("id", flat=True)
        cache.set("all_source_ids", list(all_source_ids))

    ids = set(s.id for s in sources)
    return len(set(all_source_ids) - ids) > 0


def shorten_name(name, max_length=22):
    # if the first word is too long, cut it
    words = name.split()
    if not len(words) or len(words[0]) > max_length:
        return name[:max_length]

    while len(name) > max_length:
        name = name.rsplit(None, 1)[0]

    return name


def create_default_name(objects, name):
    """
    Returns a name suffixed with a number in case similar name already exists.
    """

    names = objects.filter(name__regex=r"^{}( [0-9]+)?$".format(name)).values_list("name", flat=True)

    if len(names):
        num = len(names) + 1

        # extract suffix number from names
        nums = [int(x.replace(name, "").strip() or 1) for x in names]
        nums.sort()

        # find the first free number that is not yet used
        for i, j in enumerate(nums):
            # value can be used if index is smaller than value
            if (i + 1) < j:
                num = i + 1
                break

        if num > 1:
            name += " {}".format(num)

    return name
