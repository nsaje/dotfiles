import {FieldErrors} from '../../../shared/types/field-errors';

export interface ConversionGoalError {
    type: FieldErrors[];
    conversionWindow: FieldErrors[];
    goalId: FieldErrors[];
}
