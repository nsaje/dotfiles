import {BidModifierUploadDimensionsSummary} from './bid-modifier-upload-dimension-summary';

export interface BidModifierUploadActionSummary {
    count: number;
    dimensions: number;
    summary: BidModifierUploadDimensionsSummary[];
}
