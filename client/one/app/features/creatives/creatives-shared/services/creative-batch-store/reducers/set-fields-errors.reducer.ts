import {StoreAction} from '../../../../../../shared/services/store/store.action';
import {StoreReducer} from '../../../../../../shared/services/store/store.reducer';
import {CreativeBatchStoreState} from '../creative-batch.store.state';
import {CreativeBatchStoreFieldsErrorsState} from '../creative-batch.store.fields-errors-state';

export class SetFieldsErrorsAction extends StoreAction<
    CreativeBatchStoreFieldsErrorsState
> {}

// tslint:disable-next-line: max-classes-per-file
export class SetFieldsErrorsActionReducer extends StoreReducer<
    CreativeBatchStoreState,
    SetFieldsErrorsAction
> {
    reduce(
        state: CreativeBatchStoreState,
        action: SetFieldsErrorsAction
    ): CreativeBatchStoreState {
        return {
            ...state,
            fieldsErrors: {...action.payload},
        };
    }
}
