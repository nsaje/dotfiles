from utils import constant_base


class SubmissionFilterState(constant_base.ConstantBase):
    BLOCK = 1
    ALLOW = 2

    _VALUES = {
        BLOCK: 'Block',
        ALLOW: 'Allow',
    }
