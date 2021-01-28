import {Creative} from '../../../../../core/creatives/types/creative';
import {RequestState} from '../../../../../shared/types/request-state';
import {ScopeParams} from '../../../../../shared/types/scope-params';

export class CreativesStoreState {
    scope: ScopeParams = null;
    hasAgencyScope: boolean = null;
    entities: Creative[] = [];
    allTagsLoaded: boolean = null;
    availableTags: string[] = [];
    selectedEntityIds: string[] = [];
    requests = {
        list: {} as RequestState,
        listTags: {} as RequestState,
    };
}
