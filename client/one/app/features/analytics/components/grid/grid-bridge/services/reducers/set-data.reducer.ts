import {StoreAction} from '../../../../../../../shared/services/store/store.action';
import {StoreReducer} from '../../../../../../../shared/services/store/store.reducer';
import {Grid} from '../../types/grid';
import {GridRow} from '../../types/grid-row';
import {GridRowDataStats} from '../../types/grid-row-data';
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
                rows: action.payload.body.rows.map(this.mapToStatsRow),
                totals: [action.payload.footer.row].map(this.mapToStatsRow),
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

    private mapToStatsRow(gridRow: GridRow): GridRowDataStats {
        return {
            ...gridRow.data.stats,
            id: {value: gridRow.id},
        };
    }
}
