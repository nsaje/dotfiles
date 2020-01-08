import {RuleActionType, RuleActionFrequency} from '../rules.constants';
import {Unit} from '../../../app.constants';

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