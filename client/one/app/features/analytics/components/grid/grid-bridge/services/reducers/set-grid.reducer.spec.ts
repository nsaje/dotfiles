import {Grid} from '../../types/grid';
import {GridBridgeStoreState} from '../grid-bridge.store.state';
import {SetGridAction, SetGridActionReducer} from './set-grid.reducer';

describe('SetGridActionReducer', () => {
    let reducer: SetGridActionReducer;
    let mockedGrid: Grid;

    beforeEach(() => {
        reducer = new SetGridActionReducer();
        mockedGrid = {
            header: null,
            body: null,
            footer: null,
            meta: null,
        };
    });

    it('should correctly reduce state', () => {
        const state = reducer.reduce(
            new GridBridgeStoreState(),
            new SetGridAction(mockedGrid)
        );

        expect(state.grid).toEqual(mockedGrid);
    });
});
