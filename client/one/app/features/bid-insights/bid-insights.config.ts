import {FunnelStep} from './bid-insights.constants';

export const BID_INSIGHTS_CONFIG = {
    outletName: 'bidInsights',
    idQueryParam: 'adGroupId',
};

export const DAILY_STATS_DAYS = 30;

export const ELIGIBILITY_OK_LIMIT = 0.7;
export const ELIGIBILITY_PROBLEM_LIMIT = 0.3;

export const STEP_TO_TITLE: {
    [key in FunnelStep]: string;
} = {
    [FunnelStep.TARGETING]: 'Targeting',
    [FunnelStep.BUDGET]: 'Budget / Pacing',
    [FunnelStep.EXTERNAL_BLOCKS]: 'External Blocks',
    [FunnelStep.INTERNAL_AUCTION]: 'Internal Auction',
    [FunnelStep.RESULT]: 'Result',
};
