import {ValueModifier} from './value-modifier';
import {TimeRangeModifier} from './time-range-modifier';

export interface RuleConditionOperandModifier {
    timeRangeModifier?: TimeRangeModifier;
    valueModifier?: ValueModifier;
}
