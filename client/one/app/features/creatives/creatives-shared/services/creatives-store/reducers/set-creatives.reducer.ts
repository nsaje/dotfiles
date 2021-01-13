import {StoreAction} from '../../../../../../shared/services/store/store.action';
import {Creative} from '../../../../../../core/creatives/types/creative';
import {StoreReducer} from '../../../../../../shared/services/store/store.reducer';
import {CreativesStoreState} from '../creatives.store.state';

export class SetCreativesAction extends StoreAction<Creative[]> {}

// tslint:disable-next-line: max-classes-per-file
export class SetCreativesActionReducer extends StoreReducer<
    CreativesStoreState,
    SetCreativesAction
> {
    reduce(
        state: CreativesStoreState,
        action: SetCreativesAction
    ): CreativesStoreState {
        return {
            ...state,
            entities: action.payload,
        };
    }
}
