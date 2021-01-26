import {StoreAction} from '../../../../../../shared/services/store/store.action';
import {StoreReducer} from '../../../../../../shared/services/store/store.reducer';
import {CreativeBatchStoreState} from '../creative-batch.store.state';
import {CreativeBatch} from '../../../../../../core/creatives/types/creative-batch';

export class SetEntityAction extends StoreAction<CreativeBatch> {}

// tslint:disable-next-line: max-classes-per-file
export class SetEntityActionReducer extends StoreReducer<
    CreativeBatchStoreState,
    SetEntityAction
> {
    reduce(
        state: CreativeBatchStoreState,
        action: SetEntityAction
    ): CreativeBatchStoreState {
        return {
            ...state,
            entity: {...action.payload},
        };
    }
}
