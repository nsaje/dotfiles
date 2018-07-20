from utils.constant_base import ConstantBase


class BlueKaiCategoryStatus(ConstantBase):
    ACTIVE = 1
    INACTIVE = 2

    _VALUES = {ACTIVE: "Active", INACTIVE: "Inactive"}
