import {BidModifierType} from '../../../app.constants';

export interface BidModifier {
    id: number;
    type: BidModifierType;
    sourceSlug?: string;
    target: string;
    modifier: number;
}
