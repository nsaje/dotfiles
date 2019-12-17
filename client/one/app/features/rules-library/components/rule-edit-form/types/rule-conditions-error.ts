import {FieldErrors} from '../../../../../shared/types/field-errors';
import {RuleConditionMetricError} from './rule-condition-metric-error';
import {RuleConditionValueError} from './rule-condition-value-error';

export class RuleConditionsError {
    operator: FieldErrors = [];
    metric: RuleConditionMetricError;
    value: RuleConditionValueError;
}
