import {CampaignGoalKPI, Unit, DataType} from '../../../app.constants';

export interface CampaignGoalKPIConfig {
    name: string;
    value: CampaignGoalKPI;
    dataType: DataType;
    unit?: Unit;
}
