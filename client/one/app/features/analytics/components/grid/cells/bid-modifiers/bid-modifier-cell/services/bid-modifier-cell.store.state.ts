import {BidModifier} from '../../../../../../../../core/bid-modifiers/types/bid-modifier';
import {RequestState} from '../../../../../../../../shared/types/request-state';
import {Currency} from '../../../../../../../../app.constants';
import {BID_MODIFIER_CELL_CONFIG} from '../bid-modifier-cell.config';

export class BidModifierCellStoreState {
    adGroupId: number = null;
    value: BidModifier = {
        id: null,
        type: null,
        sourceSlug: null,
        target: null,
        modifier: null,
    };
    currency: Currency = null;
    fractionSize: number = BID_MODIFIER_CELL_CONFIG.fractionSize;
    calculatorFractionSize: number =
        BID_MODIFIER_CELL_CONFIG.calculatorFractionSize;
    modifierPercent: string = null;
    previousModifierPercent: string = null;
    requests = {
        save: {} as RequestState,
    };
}
