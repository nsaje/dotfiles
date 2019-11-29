import {BidModifierType} from '../../../app.constants';

export interface BidModifierTypeSummary {
    type: BidModifierType;
    count: number;
    min: number;
    max: number;
}
