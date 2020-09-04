import {RequestState} from '../../../../../../../../shared/types/request-state';
import {PublisherGroup} from '../../../../../../../../core/publisher-groups/types/publisher-group';
import {PublisherGroupFieldsErrorsState} from '../../../../../../../publisher-groups/types/publisher-group-fields-errors-state';

export class AddToPublishersActionStoreState {
    availablePublisherGroups: PublisherGroup[] = [];
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
        fieldsErrors: new PublisherGroupFieldsErrorsState(),
    };
    mode: 'add' | 'create' = 'add';
    requests = {
        listExplicit: {} as RequestState,
        addEntries: {} as RequestState,
    };
}
