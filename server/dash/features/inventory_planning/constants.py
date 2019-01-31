from dash.constants import ConstantBase


class InventoryDeviceType(ConstantBase):
    """
    OpenRTB values:
    --+-----------------
    1 | Mobile/Tablet
    2 | Personal Computer
    3 | Connected TV
    4 | Phone
    5 | Tablet
    6 | Connected Device
    7 | Set Top Box
    """

    PC = 2
    TV = 3
    PHONE = 4
    TABLET = 5

    _VALUES = {PC: "Desktop", TV: "TV & SetTop Box", PHONE: "Mobile", TABLET: "Tablet"}


class NativeAdServerSourceId(ConstantBase):
    MEDIAMOND = 115
    RCS = 118
    NEWSCORP = 122
    NEWSCORP_TEST = 139

    _VALUES = {
        MEDIAMOND: "Mediamond source ID",
        RCS: "RCS source ID",
        NEWSCORP: "NewsCorp source ID",
        NEWSCORP_TEST: "NewsCorp test source ID",
    }


class NativeAdServerAgencyId(ConstantBase):
    MEDIAMOND = 196
    MEDIAMOND_SELF_MANAGED = 198
    RCS_MEDIAGROUP = 220
    RCS = 186
    NEWSCORP = 86

    _VALUES = {
        MEDIAMOND: "Mediamond agency ID",
        MEDIAMOND_SELF_MANAGED: "Mediamond self managed agency ID",
        RCS_MEDIAGROUP: "RCS Mediagroup agency ID",
        RCS: "RCS agency ID",
        NEWSCORP: "NewsCorp agency ID",
    }
