import {Injectable, Injector, OnDestroy} from '@angular/core';
import {Store} from '../../../../../../shared/services/store/store';
import {StoreAction} from '../../../../../../shared/services/store/store.action';
import {StoreEffect} from '../../../../../../shared/services/store/store.effect';
import {StoreProvider} from '../../../../../../shared/services/store/store.provider';
import {StoreReducer} from '../../../../../../shared/services/store/store.reducer';
import {Grid} from '../types/grid';
import {GridColumn} from '../types/grid-column';
import {GridBridgeStoreState} from './grid-bridge.store.state';
import {
    SetColumnsAction,
    SetColumnsActionReducer,
} from './reducers/set-columns.reducer';
import {SetDataAction, SetDataActionReducer} from './reducers/set-data.reducer';
import {SetGridAction, SetGridActionReducer} from './reducers/set-grid.reducer';
import * as commonHelpers from '../../../../../../shared/helpers/common.helpers';

@Injectable()
export class GridBridgeStore extends Store<GridBridgeStoreState>
    implements OnDestroy {
    private onColumnsUpdatedHandler: Function;
    private onDataUpdatedHandler: Function;

    constructor(injector: Injector) {
        super(new GridBridgeStoreState(), injector);
    }

    ngOnDestroy() {
        super.ngOnDestroy();
        if (commonHelpers.isDefined(this.onColumnsUpdatedHandler)) {
            this.onColumnsUpdatedHandler();
        }
        if (commonHelpers.isDefined(this.onDataUpdatedHandler)) {
            this.onDataUpdatedHandler();
        }
    }

    provide(): StoreProvider<
        StoreAction<any>,
        | StoreReducer<GridBridgeStoreState, StoreAction<any>>
        | StoreEffect<GridBridgeStoreState, StoreAction<any>>
    >[] {
        return [
            {
                provide: SetGridAction,
                useClass: SetGridActionReducer,
            },
            {
                provide: SetColumnsAction,
                useClass: SetColumnsActionReducer,
            },
            {
                provide: SetDataAction,
                useClass: SetDataActionReducer,
            },
        ];
    }

    initStore(grid: Grid): void {
        this.dispatch(new SetGridAction(grid));
    }

    connect(): void {
        const api: any = this.state.grid.meta.api;
        const scope: any = this.state.grid.meta.scope;

        this.onColumnsUpdatedHandler = api.onColumnsUpdated(
            scope,
            this.handleColumnsUpdate.bind(this)
        );
        this.onDataUpdatedHandler = api.onDataUpdated(
            scope,
            this.handleDataUpdate.bind(this)
        );
    }

    private handleColumnsUpdate(): void {
        const api: any = this.state.grid.meta.api;
        const columns: GridColumn[] = api.getVisibleColumns();
        this.dispatch(new SetColumnsAction(columns));
    }

    private handleDataUpdate(): void {
        this.dispatch(new SetDataAction(this.state.grid));
    }
}
