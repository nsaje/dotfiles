import {GridBridgeStoreState} from '../grid-bridge.store.state';
import {
    SetColumnsOrderActionReducer,
    SetColumnsOrderAction,
} from './set-columns-order.reducer';

describe('SetColumnsOrderActionReducer', () => {
    let reducer: SetColumnsOrderActionReducer;
    let mockedColumns: string[];

    beforeEach(() => {
        reducer = new SetColumnsOrderActionReducer();
        mockedColumns = ['one', 'three', 'two'];
    });

    it('should correctly reduce state', () => {
        const state = reducer.reduce(
            new GridBridgeStoreState(),
            new SetColumnsOrderAction(mockedColumns)
        );

        expect(state.columnsOrder).toEqual(['one', 'three', 'two']);
    });
});
