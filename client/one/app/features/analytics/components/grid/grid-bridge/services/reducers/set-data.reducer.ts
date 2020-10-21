import {StoreAction} from '../../../../../../../shared/services/store/store.action';
import {StoreReducer} from '../../../../../../../shared/services/store/store.reducer';
import {Grid} from '../../types/grid';
import {GridBridgeStoreState} from '../grid-bridge.store.state';

export class SetDataAction extends StoreAction<Grid> {}

// tslint:disable-next-line: max-classes-per-file
export class SetDataActionReducer extends StoreReducer<
    GridBridgeStoreState,
    SetDataAction
> {
    reduce(
        state: GridBridgeStoreState,
        action: SetDataAction
    ): GridBridgeStoreState {
        return {
            ...state,
            data: {
                ...state.data,
                rows: [...action.payload.body.rows],
                totals: [{...action.payload.footer.row}],
                pagination: {
                    ...state.data.pagination,
                    ...action.payload.body.pagination,
                },
                paginationOptions: {
                    ...state.data.paginationOptions,
                    ...action.payload.meta.paginationOptions,
                },
            },
        };
    }
}
