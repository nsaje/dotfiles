from utils.constant_base import ConstantBase


class Alert(ConstantBase):
    OK = 0
    EXECUTION = 1
    DURATION = 2
    FAILURE = 3

    _VALUES = {OK: "OK", EXECUTION: "Execution", DURATION: "Duration", FAILURE: "Failure"}
