import {Account} from '../../../../core/entities/types/account/account';
import {RequestState} from '../../../../shared/types/request-state';
import {Rule} from '../../../../core/rules/types/rule';
import {RulesStoreFieldsErrorsState} from './rule.store.fields-errors-state';

export class RulesStoreState {
    agencyId: string = null;
    accountId: string = null;
    hasAgencyScope: boolean = null;
    activeEntity = {
        entity: {} as Partial<Rule>,
        isReadOnly: null as boolean,
    };
    entities: Rule[] = [];
    fieldsErrors: RulesStoreFieldsErrorsState[] = [];
    requests = {
        list: {} as RequestState,
    };
}
