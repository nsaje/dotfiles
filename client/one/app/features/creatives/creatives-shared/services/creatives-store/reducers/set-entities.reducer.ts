import {StoreAction} from '../../../../../../shared/services/store/store.action';
import {Creative} from '../../../../../../core/creatives/types/creative';
import {StoreReducer} from '../../../../../../shared/services/store/store.reducer';
import {CreativesStoreState} from '../creatives.store.state';

export class SetEntitiesAction extends StoreAction<Creative[]> {}

// tslint:disable-next-line: max-classes-per-file
export class SetEntitiesActionReducer extends StoreReducer<
    CreativesStoreState,
    SetEntitiesAction
> {
    reduce(
        state: CreativesStoreState,
        action: SetEntitiesAction
    ): CreativesStoreState {
        return {
            ...state,
            entities: [...action.payload],
        };
    }
}
