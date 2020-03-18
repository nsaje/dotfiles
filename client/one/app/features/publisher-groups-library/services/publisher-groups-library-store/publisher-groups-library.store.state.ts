import {PublisherGroup} from '../../../../core/publisher-groups/types/publisher-group';
import {PublisherGroupsLibraryStoreFieldsErrorsState} from './publisher-groups-library.store.fields-errors-state';
import {RequestState} from '../../../../shared/types/request-state';

export class PublisherGroupsLibraryStoreState {
    accountId: string = null;
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
        fieldErrors: new PublisherGroupsLibraryStoreFieldsErrorsState(),
    };
    requests = {
        search: {} as RequestState,
        list: {} as RequestState,
        upload: {} as RequestState,
    };
}
