import {StoreAction} from '../../../../../../shared/services/store/store.action';
import {StoreReducer} from '../../../../../../shared/services/store/store.reducer';
import {CreativeTagsStoreState} from '../creative-tags-store.state';

export class SetAvailableTagsAction extends StoreAction<{
    allTagsLoaded: boolean;
    availableTags: string[];
}> {}

// tslint:disable-next-line: max-classes-per-file
export class SetAvailableTagsActionReducer extends StoreReducer<
    CreativeTagsStoreState,
    SetAvailableTagsAction
> {
    reduce(
        state: CreativeTagsStoreState,
        action: SetAvailableTagsAction
    ): CreativeTagsStoreState {
        return {
            ...state,
            availableTags: action.payload.availableTags,
            allTagsLoaded: action.payload.allTagsLoaded,
        };
    }
}
