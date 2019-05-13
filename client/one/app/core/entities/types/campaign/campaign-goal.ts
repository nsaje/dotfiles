import {CampaignGoalKPI} from '../../../../app.constants';
import {CampaignConversionGoal} from './campaign-conversion-goal';

export interface CampaignGoal {
    id: string;
    type: CampaignGoalKPI;
    value: string;
    primary: boolean;
    conversionGoal: CampaignConversionGoal;
}
