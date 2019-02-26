class BidModifierInvalid(Exception):
    pass


class BidModifierValueInvalid(BidModifierInvalid):
    pass


class BidModifierSourceInvalid(BidModifierInvalid):
    pass


class InvalidBidModifierFile(Exception):
    pass
