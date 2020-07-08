import {RuleHistory} from '../../../../core/rules/types/rule-history';
import {RequestState} from '../../../../shared/types/request-state';
import {Rule} from '../../../../core/rules/types/rule';
import {AdGroup} from '../../../../core/entities/types/ad-group/ad-group';

export class RulesHistoriesStoreState {
    agencyId: string = null;
    accountId: string = null;
    entities: RuleHistory[] = [];

    rules: Rule[] = [];
    adGroups: AdGroup[] = [];

    requests = {
        list: {} as RequestState,
        listHistories: {} as RequestState,
    };

    adGroupRequests = {
        list: {} as RequestState,
    };
}
