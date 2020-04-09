import {PublisherGroup} from '../../../../core/publisher-groups/types/publisher-group';
import {Account} from '../../../../core/entities/types/account/account';
import {PublisherGroupsLibraryStoreFieldsErrorsState} from './publisher-groups-library.store.fields-errors-state';
import {RequestState} from '../../../../shared/types/request-state';
import {ScopeSelectorState} from '../../../../shared/components/scope-selector/scope-selector.constants';

export class PublisherGroupsLibraryStoreState {
    agencyId: string = null;
    accountId: string = null;
    hasAgencyScope: boolean = null;
    entities: PublisherGroup[] = [];
    systemEntities: PublisherGroup[] = [];
    activeEntity = {
        entity: {
            id: null,
            name: null,
            accountId: null,
            agencyId: null,
            includeSubdomains: null,
            implicit: null,
            modified: null,
            created: null,
            type: null,
            level: null,
            levelName: null,
            levelId: null,
            entries: null,
        } as PublisherGroup,
        scopeState: null as ScopeSelectorState,
        isReadOnly: null as boolean,
        fieldsErrors: new PublisherGroupsLibraryStoreFieldsErrorsState(),
    };
    accounts: Account[] = [];
    accountsRequests = {
        list: {} as RequestState,
    };
    requests = {
        search: {} as RequestState,
        list: {} as RequestState,
        upload: {} as RequestState,
    };
}
