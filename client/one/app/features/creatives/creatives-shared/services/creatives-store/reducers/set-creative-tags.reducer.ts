import {StoreAction} from '../../../../../../shared/services/store/store.action';
import {StoreReducer} from '../../../../../../shared/services/store/store.reducer';
import {CreativesStoreState} from '../creatives.store.state';
import {ScopeParams} from '../../../../../../shared/types/scope-params';
import {PaginationState} from '../../../../../../shared/components/smart-grid/types/pagination-state';
import {CreativeTagsSearchParams} from '../../../types/creative-tags-search-params';
import {RequestStateUpdater} from '../../../../../../shared/types/request-state-updater';

export interface SetCreativeTagsParams {
    tags: string[];
    allTagsLoaded: boolean;
}

export class SetCreativeTagsAction extends StoreAction<SetCreativeTagsParams> {}

// tslint:disable-next-line: max-classes-per-file
export class SetCreativeTagsActionReducer extends StoreReducer<
    CreativesStoreState,
    SetCreativeTagsAction
> {
    reduce(
        state: CreativesStoreState,
        action: SetCreativeTagsAction
    ): CreativesStoreState {
        return {
            ...state,
            availableTags: action.payload.tags,
            allTagsLoaded: action.payload.allTagsLoaded,
        };
    }
}
