import {
    GridRenderingEngineType,
    GridRowLevel,
    GridRowType,
} from '../../../../../analytics.constants';
import {Grid} from '../../types/grid';
import {GridBridgeStoreState} from '../grid-bridge.store.state';
import {SetDataAction, SetDataActionReducer} from './set-data.reducer';

describe('SetDataActionReducer', () => {
    let reducer: SetDataActionReducer;
    let mockedGrid: Grid;

    beforeEach(() => {
        reducer = new SetDataActionReducer();
        mockedGrid = {
            header: null,
            body: {
                rows: [
                    {
                        id: 'test',
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
                    id: 'test',
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
                api: null,
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

    it('should correctly reduce state', () => {
        const state = reducer.reduce(
            new GridBridgeStoreState(),
            new SetDataAction(mockedGrid)
        );

        expect(state.data).toEqual({
            rows: [
                {
                    test_field: {
                        value: 'TEST VALUE',
                    },
                },
            ] as any[],
            totals: [
                {
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
    });
});
