import {
    RuleActionType,
    RuleActionFrequency,
    Unit,
} from '../rule-form.constants';

export interface RuleActionConfig {
    label: string;
    type: RuleActionType;
    frequencies: RuleActionFrequency[];
    hasValue?: boolean;
    unit?: Unit;
    hasLimit?: boolean;
    limitLabel?: string;
    limitDescription?: string;
}
