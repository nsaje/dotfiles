import {Deal} from '../../../../core/deals/types/deal';
import {DealConnection} from '../../../../core/deals/types/deal-connection';
import {RequestState} from '../../../../shared/types/request-state';
import {DealsLibraryStoreFieldsErrorsState} from './deals-library.store.fields-errors-state';

export class DealsLibraryStoreState {
    entities: Deal[] = [];
    fieldsErrors: DealsLibraryStoreFieldsErrorsState[] = [];
    activeEntity = {
        entity: {
            id: null,
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
        connections: [] as DealConnection[],
        fieldsErrors: new DealsLibraryStoreFieldsErrorsState(),
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