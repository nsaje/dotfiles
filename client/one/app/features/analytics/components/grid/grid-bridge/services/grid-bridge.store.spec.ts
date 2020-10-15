import {Injector} from '@angular/core';
import {fakeAsync, TestBed, tick} from '@angular/core/testing';
import {ColDef} from 'ag-grid-community';
import {StoreAction} from '../../../../../../shared/services/store/store.action';
import {StoreEffect} from '../../../../../../shared/services/store/store.effect';
import {StoreProvider} from '../../../../../../shared/services/store/store.provider';
import {StoreReducer} from '../../../../../../shared/services/store/store.reducer';
import {
    GridColumnTypes,
    GridRenderingEngineType,
    GridRowLevel,
    GridRowType,
} from '../../../../analytics.constants';
import {GRID_API_DEBOUNCE_TIME} from '../grid-bridge.component.constants';
import {Grid} from '../types/grid';
import {GridColumn} from '../types/grid-column';
import {GridColumnOrder} from '../types/grid-column-order';
import {GridBridgeStore} from './grid-bridge.store';
import {GridBridgeStoreState} from './grid-bridge.store.state';
import {
    SetColumnsAction,
    SetColumnsActionReducer,
} from './reducers/set-columns.reducer';
import {SetDataAction, SetDataActionReducer} from './reducers/set-data.reducer';
import {SetGridAction, SetGridActionReducer} from './reducers/set-grid.reducer';

class SetTestColumnsActionReducer extends SetColumnsActionReducer {
    reduce(
        state: GridBridgeStoreState,
        action: SetColumnsAction
    ): GridBridgeStoreState {
        return {
            ...state,
            columns: action.payload.map(column => this.map(column)),
        };
    }

    private map(column: GridColumn): ColDef {
        return {
            headerName: column.data.name,
            field: column.data.field,
        };
    }
}

// tslint:disable-next-line: max-classes-per-file
class TestGridBridgeStore extends GridBridgeStore {
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
                useClass: SetTestColumnsActionReducer,
            },
            {
                provide: SetDataAction,
                useClass: SetDataActionReducer,
            },
        ];
    }
}

describe('GridBridgeStore', () => {
    let store: TestGridBridgeStore;
    let mockedGrid: Grid;
    let mockedVisibleColumns: GridColumn[];

    beforeEach(() => {
        store = new TestGridBridgeStore(TestBed.get(Injector));

        mockedVisibleColumns = [
            {
                type: GridColumnTypes.TEXT,
                field: '',
                data: {
                    name: 'Test',
                    field: 'test_field',
                    internal: false,
                    shown: true,
                    totalRow: true,
                    type: GridColumnTypes.TEXT,
                },
                visible: true,
                disabled: false,
                order: GridColumnOrder.DESC,
            },
        ];
        mockedGrid = {
            header: {
                columns: [],
            },
            body: {
                rows: [
                    {
                        id: 'row',
                        type: GridRowType.STATS,
                        entity: null,
                        data: {
                            stats: {
                                test_field: {
                                    value: 'TEST VALUE',
                                },
                            },
                        },
                        level: GridRowLevel.BASE,
                        parent: null,
                        collapsed: true,
                        visible: true,
                    },
                ],
                pagination: {
                    complete: true,
                    offset: 0,
                    limit: 1,
                    count: 1,
                },
            },
            footer: {
                row: {
                    id: 'totals',
                    type: GridRowType.STATS,
                    entity: null,
                    data: {
                        stats: {
                            test_field: {
                                value: 'TOTALS OF TEST VALUE',
                            },
                        },
                    },
                    level: GridRowLevel.BASE,
                    parent: null,
                    collapsed: true,
                    visible: true,
                },
            },
            meta: {
                initialized: true,
                loading: false,
                renderingEngine: GridRenderingEngineType.SMART_GRID,
                paginationOptions: {type: 'server', page: 1, pageSize: 10},
                options: null,
                api: {
                    onColumnsUpdated: (scope: any, handlerFn: Function) => {
                        handlerFn();
                    },
                    onDataUpdated: (scope: any, handlerFn: Function) => {
                        handlerFn();
                    },
                    getVisibleColumns: () => {
                        return mockedVisibleColumns;
                    },
                },
                dataService: null,
                columnsService: null,
                orderService: null,
                collapseService: null,
                selectionService: null,
                pubsub: null,
                data: null,
                scope: null,
            },
        };
    });

    it('should correctly reduce grid', () => {
        expect(store.state.grid).toEqual(null);
        store.initStore(mockedGrid);
        expect(store.state.grid).toEqual(mockedGrid);
    });

    it('should correctly reduce grid columns', fakeAsync(() => {
        store.initStore(mockedGrid);
        store.connect();
        tick(GRID_API_DEBOUNCE_TIME);
        expect(store.state.columns).toEqual([
            {
                headerName: 'Test',
                field: 'test_field',
            },
        ]);
    }));

    it('should correctly reduce grid data', fakeAsync(() => {
        store.initStore(mockedGrid);
        store.connect();
        tick(GRID_API_DEBOUNCE_TIME);
        expect(store.state.data).toEqual({
            rows: [
                {
                    id: {
                        value: 'row',
                    },
                    test_field: {
                        value: 'TEST VALUE',
                    },
                },
            ] as any[],
            totals: [
                {
                    id: {
                        value: 'totals',
                    },
                    test_field: {
                        value: 'TOTALS OF TEST VALUE',
                    },
                },
            ] as any[],
            paginationOptions: {
                type: 'server',
                page: 1,
                pageSize: 10,
            },
            pagination: {
                complete: true,
                offset: 0,
                limit: 1,
                count: 1,
            },
        });
    }));
});
