import {StoreAction} from '../../../../../../shared/services/store/store.action';
import {StoreReducer} from '../../../../../../shared/services/store/store.reducer';
import {CreativesStoreState} from '../creatives.store.state';

export class SetCreativeTagsAction extends StoreAction<string[]> {}

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
            availableTags: action.payload,
        };
    }
}
