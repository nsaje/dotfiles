import {BidModifier} from './bid-modifier';
import {BidModifierUpdateAction} from '../../../app.constants';

export interface BidModifierUpdate {
    adGroupId: number;
    bidModifier: BidModifier;
    action: BidModifierUpdateAction;
}
