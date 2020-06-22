import {RuleHistory} from '../../../../core/rules/types/rule-history';
import {RequestState} from '../../../../shared/types/request-state';

export class RulesHistoriesStoreState {
    agencyId: string = null;
    accountId: string = null;
    entities: RuleHistory[] = [];
    requests = {
        listHistories: {} as RequestState,
    };
}
