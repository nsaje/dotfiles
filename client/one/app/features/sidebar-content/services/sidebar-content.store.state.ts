import {RequestState} from '../../../shared/types/request-state';
import {Agency} from '../../../core/entities/types/agency/agency';
import {Account} from '../../../core/entities/types/account/account';

export class SidebarContentStoreState {
    selectedAgencyId: string = null;
    selectedAccountId: string = null;
    agencies = [] as Agency[];
    accounts = [] as Account[];
    agenciesRequests = {
        list: {} as RequestState,
    };
    accountsRequests = {
        list: {} as RequestState,
    };
}
