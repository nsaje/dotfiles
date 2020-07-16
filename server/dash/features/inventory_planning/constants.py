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


class InventoryChannel(ConstantBase):
    NATIVE = "native"
    VIDEO = "video"
    NATIVE_OR_VIDEO = "nativeorvideo"
    DISPLAY = "display"

    _VALUES = {NATIVE: "Native", VIDEO: "Video", NATIVE_OR_VIDEO: "Native or Video", DISPLAY: "Display"}
