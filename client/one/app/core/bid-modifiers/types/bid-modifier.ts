import {BidModifierType} from '../../../app.constants';

export interface BidModifier {
    id: number;
    type: BidModifierType;
    sourceSlug?: string;
    target: string;
    bidMin: string;
    bidMax: string;
    modifier: number;
}
