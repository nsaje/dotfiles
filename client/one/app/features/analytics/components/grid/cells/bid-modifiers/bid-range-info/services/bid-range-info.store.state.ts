import {BidModifier} from '../../../../../../../../core/bid-modifiers/types/bid-modifier';
import {
    Currency,
    BiddingType,
    AdGroupAutopilotState,
} from '../../../../../../../../app.constants';
import {BidModifierTypeSummary} from '../../../../../../../../core/bid-modifiers/types/bid-modifier-type-summary';
import {TypeSummaryGridRow} from '../../../../../../../../shared/components/bid-modifier-types-grid/services/type-summary-grid-row';

export class BidRangeInfoStoreState {
    bidModifier: BidModifier = {
        id: null,
        type: null,
        sourceSlug: null,
        target: null,
        modifier: null,
    };
    bid: string;
    biddingType: BiddingType;
    bidModifierTypeSummaries: BidModifierTypeSummary[];
    sourceBidModifierTypeSummary: BidModifierTypeSummary = null; // TODO: RTAP: remove this after Phase 1
    bidModifierTypeGridRows: TypeSummaryGridRow[];
    currency: Currency = null;
    fractionSize: number = null;
    adGroupAutopilotState: AdGroupAutopilotState = null;
    autopilot: boolean = null;
    minFactor: number = null;
    maxFactor: number = null;
    computedBidMin: string = null;
    computedBidMax: string = null;
    infoMessage: string = null;
    selectionTooltipMessage: string = null;
    bidMessage: string = null;
    formattedBidValueRange: string = null;
    finalBidRangeMessage: string = null;
    finalBidRangeValue: string = null;
    agencyUsesRealtimeAutopilot: boolean = false;
}
