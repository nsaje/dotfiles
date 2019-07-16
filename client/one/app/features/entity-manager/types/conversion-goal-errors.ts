import {FieldErrors} from '../../../shared/types/field-errors';

export interface ConversionGoalErrors {
    type: FieldErrors;
    conversionWindow: FieldErrors;
    goalId: FieldErrors;
}
