import {ScopeParams} from '../../../../../shared/types/scope-params';
import {RequestState} from '../../../../../shared/types/request-state';

export class CreativeTagsStoreState {
    scope: ScopeParams = null;
    allTagsLoaded: boolean = false;
    availableTags: string[] = [];
    requests = {
        list: {} as RequestState,
    };
}
