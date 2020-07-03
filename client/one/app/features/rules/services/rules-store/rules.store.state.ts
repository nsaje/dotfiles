import {Account} from '../../../../core/entities/types/account/account';
import {RequestState} from '../../../../shared/types/request-state';
import {Rule} from '../../../../core/rules/types/rule';
import {RulesStoreFieldsErrorsState} from './rule.store.fields-errors-state';

export class RulesStoreState {
    agencyId: string = null;
    accountId: string = null;
    hasAgencyScope: boolean = null;
    entities: Rule[] = [];
    fieldsErrors: RulesStoreFieldsErrorsState[] = [];
    accounts: Account[] = [];
    accountsRequests = {
        list: {} as RequestState,
    };
    requests = {
        list: {} as RequestState,
    };
}
