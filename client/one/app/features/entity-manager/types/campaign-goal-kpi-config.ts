import {CampaignGoalKPI} from '../../../app.constants';

export interface CampaignGoalKPIConfig {
    name: string;
    value: CampaignGoalKPI;
    unit?: string;
    isCurrency?: boolean;
}
