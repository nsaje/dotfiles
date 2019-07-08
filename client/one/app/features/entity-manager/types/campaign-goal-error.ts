import {FieldErrors} from '../../../shared/types/field-errors';
import {ConversionGoalError} from './conversion-goal-error';

export interface CampaignGoalError {
    type: FieldErrors[];
    value: FieldErrors[];
    conversionGoal: ConversionGoalError;
}
