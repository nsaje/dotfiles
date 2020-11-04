import {
    AdGroupAutopilotState,
    AdGroupSettingsAutopilotState,
    BiddingType,
    Breakdown,
    Currency,
    Level,
} from '../../../../../../app.constants';
import {BidModifierTypeSummary} from '../../../../../../core/bid-modifiers/types/bid-modifier-type-summary';

export interface GridMetaData {
    id?: number;
    level?: Level;
    breakdown?: Breakdown;
    ext?: GridMetaDataExt;
    campaignAutopilot?: boolean;
    adGroupAutopilotState?: AdGroupSettingsAutopilotState;
}

export interface GridMetaDataExt {
    autopilotState?: AdGroupAutopilotState;
    currency?: Currency;
    biddingType?: BiddingType;
    bid?: string;
    typeSummaries?: BidModifierTypeSummary[];
    agencyUsesRealtimeAutopilot?: boolean;
}
