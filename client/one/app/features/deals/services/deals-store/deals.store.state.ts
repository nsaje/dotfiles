import {Deal} from '../../../../core/deals/types/deal';
import {Source} from '../../../../core/sources/types/source';
import {Account} from '../../../../core/entities/types/account/account';
import {DealConnection} from '../../../../core/deals/types/deal-connection';
import {RequestState} from '../../../../shared/types/request-state';
import {DealsStoreFieldsErrorsState} from './deals.store.fields-errors-state';
import {ScopeSelectorState} from '../../../../shared/components/scope-selector/scope-selector.constants';

export class DealsStoreState {
    agencyId: string = null;
    accountId: string = null;
    hasAgencyScope: boolean = null;
    entities: Deal[] = [];
    fieldsErrors: DealsStoreFieldsErrorsState[] = [];
    activeEntity = {
        entity: {
            id: null,
            agencyId: null,
            accountId: null,
            dealId: null,
            description: null,
            name: null,
            source: null,
            floorPrice: null,
            validFromDate: null,
            validToDate: null,
            createdDt: null,
            modifiedDt: null,
            createdBy: null,
            numOfAccounts: null,
            numOfCampaigns: null,
            numOfAdgroups: null,
        } as Deal,
        scopeState: null as ScopeSelectorState,
        isReadOnly: null as boolean,
        connections: [] as DealConnection[],
        fieldsErrors: new DealsStoreFieldsErrorsState(),
    };
    accounts: Account[] = [];
    accountsRequests = {
        list: {} as RequestState,
    };
    sources: Source[] = [];
    sourcesRequests = {
        list: {} as RequestState,
    };
    requests = {
        list: {} as RequestState,
        create: {} as RequestState,
        edit: {} as RequestState,
        validate: {} as RequestState,
        get: {} as RequestState,
        remove: {} as RequestState,
        listConnections: {} as RequestState,
        removeConnection: {} as RequestState,
    };
}
