import {TimeRange} from '../rule-form.constants';
import {ValueModifier} from './value-modifier';

export interface RuleConditionOperandModifier {
    timeRange?: TimeRange;
    valueModifier?: ValueModifier;
}
