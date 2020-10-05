import {StoreAction} from '../../../../../../../shared/services/store/store.action';
import {StoreReducer} from '../../../../../../../shared/services/store/store.reducer';
import {Grid} from '../../types/grid';
import {GridBridgeStoreState} from '../grid-bridge.store.state';

export class SetGridAction extends StoreAction<Grid> {}

// tslint:disable-next-line: max-classes-per-file
export class SetGridActionReducer extends StoreReducer<
    GridBridgeStoreState,
    SetGridAction
> {
    reduce(
        state: GridBridgeStoreState,
        action: SetGridAction
    ): GridBridgeStoreState {
        return {
            ...state,
            grid: action.payload,
        };
    }
}
