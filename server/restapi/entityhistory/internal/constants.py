from utils.constant_base import ConstantBase


class EntityHistoryOrder(ConstantBase):
    CREATED_DT_ASC = "created_dt"
    CREATED_BY_ASC = "created_by"
    CREATED_DT_DESC = "-created_dt"
    CREATED_BY_DESC = "-created_by"

    _VALUES = {
        CREATED_DT_ASC: "Created Date ASC",
        CREATED_BY_ASC: "Created By ASC",
        CREATED_DT_DESC: "Created Date DESC",
        CREATED_BY_DESC: "Created By DESC",
    }
