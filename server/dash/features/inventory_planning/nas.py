NAS_MAPPING = {  # source id to a list of agency ids whose users have access to this source
    115: [196, 198],  # mediamond
    118: [220, 186],  # rcs
    122: [86],  # newscorp
    139: [86],  # newscorp test
    169: [491],  # zurnal24
    127: [275],  # pop tv
    163: [440],  # prisa
    162: [443],  # adria media
    171: [408],  # rossel
    172: [525],  # friday media group
    182: [580],  # mediahuis
    183: [617],  # sud oest
}


def should_show_nas_source(source, request):
    if source.id not in NAS_MAPPING:
        return False
    if request is None or request.user.has_perm("zemauth.can_see_all_nas_in_inventory_planning"):
        return True
    return request.user.agency_set.filter(id__in=NAS_MAPPING[source.id]).exists()
