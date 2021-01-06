import {StoreAction} from '../../../../../../../shared/services/store/store.action';
import {StoreReducer} from '../../../../../../../shared/services/store/store.reducer';
import {GridBridgeStoreState} from '../grid-bridge.store.state';

export class SetColumnsOrderAction extends StoreAction<string[]> {}

// tslint:disable-next-line: max-classes-per-file
export class SetColumnsOrderActionReducer extends StoreReducer<
    GridBridgeStoreState,
    SetColumnsOrderAction
> {
    reduce(
        state: GridBridgeStoreState,
        action: SetColumnsOrderAction
    ): GridBridgeStoreState {
        return {
            ...state,
            columnsOrder: [...action.payload],
        };
    }
}
