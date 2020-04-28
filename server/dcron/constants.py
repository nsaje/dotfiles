from utils.constant_base import ConstantBase


class Alert(ConstantBase):
    OK = 0
    EXECUTION = 1
    DURATION = 2
    FAILURE = 3

    _VALUES = {OK: "OK", EXECUTION: "Execution", DURATION: "Duration", FAILURE: "Failure"}
    _DESCRIPTIONS = {
        OK: "The job is executing OK now.",
        EXECUTION: "The job missed a scheduled execution. Check 'dcron' app admin or 'Z1 Cron Jobs' in Grafana.",
        DURATION: "The job is executing too long. Check 'dcron' app admin or 'Z1 Cron Jobs' in Grafana.",
        FAILURE: "The job execution failed. Check LogDNA for details.",
    }

    @classmethod
    def get_description(cls, cons):
        return cls._DESCRIPTIONS.get(cons)


class Severity(ConstantBase):
    LOW = 0
    HIGH = 1

    _VALUES = {LOW: "low", HIGH: "high"}


class Ownership(ConstantBase):
    Z1 = 1
    PRODOPS = 2

    _VALUES = {Z1: "Z1", PRODOPS: "ProdOps"}
