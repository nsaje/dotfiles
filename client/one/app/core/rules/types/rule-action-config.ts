import {RuleActionType, RuleActionFrequency} from '../rules.constants';
import {Unit} from '../../../app.constants';

export interface RuleActionConfig {
    description?: string;
    type: RuleActionType;
    valueLabel?: string;
    frequencies: RuleActionFrequency[];
    hasValue?: boolean;
    unit?: Unit;
    hasLimit?: boolean;
    limitLabel?: string;
    limitDescription?: string;
    hasPublisherGroupSelector?: boolean;
}
