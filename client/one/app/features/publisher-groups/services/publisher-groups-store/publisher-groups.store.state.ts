import {PublisherGroup} from '../../../../core/publisher-groups/types/publisher-group';
import {Account} from '../../../../core/entities/types/account/account';
import {PublisherGroupFieldsErrorsState} from '../../types/publisher-group-fields-errors-state';
import {RequestState} from '../../../../shared/types/request-state';
import {ScopeSelectorState} from '../../../../shared/components/scope-selector/scope-selector.constants';
import {PaginationOptions} from '../../../../shared/components/smart-grid/types/pagination-options';
import {PublisherGroupConnection} from '../../../../core/publisher-groups/types/publisher-group-connection';

export class PublisherGroupsStoreState {
    agencyId: string = null;
    accountId: string = null;
    hasAgencyScope: boolean = null;
    explicitEntities: PublisherGroup[] = [];
    implicitEntities: PublisherGroup[] = [];
    explicitPaginationOptions: PaginationOptions;
    implicitPaginationOptions: PaginationOptions;
    activeEntity = {
        entity: {
            id: null,
            name: null,
            accountId: null,
            agencyId: null,
            includeSubdomains: null,
            implicit: null,
            size: null,
            modifiedDt: null,
            createdDt: null,
            type: null,
            level: null,
            levelName: null,
            levelId: null,
            entries: null,
        } as PublisherGroup,
        scopeState: null as ScopeSelectorState,
        isReadOnly: null as boolean,
        connections: [] as PublisherGroupConnection[],
        fieldsErrors: new PublisherGroupFieldsErrorsState(),
    };
    accounts: Account[] = [];
    accountsRequests = {
        list: {} as RequestState,
    };
    requests = {
        listExplicit: {} as RequestState,
        listImplicit: {} as RequestState,
        upload: {} as RequestState,
        listConnections: {} as RequestState,
        removeConnection: {} as RequestState,
    };
}
