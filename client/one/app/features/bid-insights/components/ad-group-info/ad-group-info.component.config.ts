import {AdGroupInfoStep} from '../../bid-insights.constants';

export const STEP_TO_TITLE: {
    [key in AdGroupInfoStep]: string;
} = {
    [AdGroupInfoStep.TARGETING]: 'Targeting',
    [AdGroupInfoStep.BUDGET]: 'Budget / Pacing',
    [AdGroupInfoStep.EXTERNAL_BLOCKS]: 'External Blocks',
    [AdGroupInfoStep.INTERNAL_AUCTION]: 'Internal Auction',
};

export const ITEM_LENGTH_DISPLAY_LIMIT = 40;
