import {BidModifier} from '../../../../../../core/bid-modifiers/types/bid-modifier';
import {RequestState} from '../../../../../../shared/types/request-state';
import {Currency} from '../../../../../../app.constants';

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
    currency: Currency = null;
    modifierPercent: string = null;
    previousModifierPercent: string = null;
    computedBidMin: string = null;
    computedBidMax: string = null;
    requests = {
        save: {} as RequestState,
    };
}
