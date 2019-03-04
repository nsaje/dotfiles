import {BidModifier} from '../../../../../../core/bid-modifiers/types/bid-modifier';
import {BidModifierRequests} from '../../../../../../core/bid-modifiers/types/bid-modifier-requests';

export class BidModifierCellStoreState {
    adGroupId: number = null;
    value: BidModifier = {
        id: null,
        type: null,
        sourceSlug: null,
        target: null,
        bidMin: null,
        bidMax: null,
        modifier: null,
    };
    currency: string = null;
    modifierPercent: string = null;
    previousModifierPercent: string = null;
    computedBidMin: string = null;
    computedBidMax: string = null;
    requests: BidModifierRequests = {
        save: {},
    };
}
