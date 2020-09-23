import {FieldErrors} from '../../../../../shared/types/field-errors';

export class RuleConditionMetricError {
    window: FieldErrors = [];
    type: FieldErrors = [];
    modifier: FieldErrors = [];
    conversionPixel: FieldErrors = [];
    conversionPixelWindow: FieldErrors = [];
    conversionPixelAttribution: FieldErrors = [];
}
