class BidModifierInvalid(Exception):
    pass


class BidModifierValueInvalid(BidModifierInvalid):
    pass


class BidModifierValueTooHigh(BidModifierValueInvalid):
    pass


class BidModifierValueTooLow(BidModifierValueInvalid):
    pass


class BidModifierTargetInvalid(BidModifierInvalid):
    pass


class BidModifierSourceInvalid(BidModifierInvalid):
    pass


class BidModifierTypeInvalid(BidModifierInvalid):
    pass


class BidModifierUnsupportedTarget(BidModifierInvalid):
    pass


class InvalidBidModifierFile(Exception):
    pass


class BidModifierDeleteInvalidIds(Exception):
    pass
