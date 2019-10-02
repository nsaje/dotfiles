import {Deal} from '../../../../core/deals/types/deal';
import {DealConnection} from '../../../../core/deals/types/deal-connection';
import {RequestState} from '../../../../shared/types/request-state';
import {DealStoreFieldsErrorsState} from './deals-library.store.fields-errors-state';

export class DealsStoreState {
    entities: Deal[] = [];
    fieldsErrors: DealStoreFieldsErrorsState[] = [];
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
        fieldsErrors: new DealStoreFieldsErrorsState(),
    };
    request = {
        list: {} as RequestState,
        save: {} as RequestState,
        validate: {} as RequestState,
        get: {} as RequestState,
        remove: {} as RequestState,
        listConnections: {} as RequestState,
        removeConnection: {} as RequestState,
    };
}
