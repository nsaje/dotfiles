import {FunnelStep} from '../bid-insights.constants';

export interface AdGroupIssue {
    [FunnelStep.TARGETING]: string;
    [FunnelStep.BUDGET]: string;
    [FunnelStep.EXTERNAL_BLOCKS]: string;
    [FunnelStep.INTERNAL_AUCTION]: string;
    [FunnelStep.RESULT]: string;
}
