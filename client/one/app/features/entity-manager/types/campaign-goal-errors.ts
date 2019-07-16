import {FieldErrors} from '../../../shared/types/field-errors';
import {ConversionGoalErrors} from './conversion-goal-errors';

export interface CampaignGoalErrors {
    type: FieldErrors;
    value: FieldErrors;
    conversionGoal: ConversionGoalErrors;
}
