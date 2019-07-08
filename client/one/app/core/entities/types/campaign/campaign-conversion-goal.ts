import {
    CampaignConversionGoalType,
    ConversionWindow,
} from '../../../../app.constants';

export interface CampaignConversionGoal {
    type: CampaignConversionGoalType;
    conversionWindow: ConversionWindow;
    goalId: string;
    pixelUrl?: string;
    name?: string;
}
