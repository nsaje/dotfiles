import {RuleHistoryStatus} from '../rules.constants';

export interface RuleHistory {
    id: string;
    createdDt: Date;
    status: RuleHistoryStatus;
    changes: string | null;
    changesText: string | null;
    changesFormatted: string | null;
    ruleId: string;
    ruleName: string;
    adGroupId: string;
    adGroupName: string;
}
