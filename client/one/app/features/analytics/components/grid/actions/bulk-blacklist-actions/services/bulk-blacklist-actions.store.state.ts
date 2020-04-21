import {RequestState} from '../../../../../../../shared/types/request-state';

export class BulkBlacklistActionsStoreState {
    requests = {
        updateBlacklistStatuses: {} as RequestState,
    };
}
