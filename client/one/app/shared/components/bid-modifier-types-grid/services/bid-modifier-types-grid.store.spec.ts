import {BidModifierTypesGridStore} from './bid-modifier-types-grid.store';
import {GridOptions} from 'ag-grid-community';

describe('BidModifierTypesGridStore', () => {
    let store: BidModifierTypesGridStore;

    beforeEach(() => {
        store = new BidModifierTypesGridStore();
    });

    it('should be correctly initialized for settings bid modifier overview', () => {
        const showCountColumn = true;
        const selectableRows = false;
        const selectionTooltip = 'Tooltip message';

        store.updateGridConfig(
            showCountColumn,
            selectableRows,
            selectionTooltip
        );
        expect(store.state.showCountColumn).toEqual(showCountColumn);
        expect(store.state.selectableRows).toEqual(selectableRows);
        expect(store.state.selectionTooltip).toEqual(selectionTooltip);
        expect(store.state.gridOptions).toEqual({
            suppressMovableColumns: true,
        } as GridOptions);

        const columnHeaders = store.state.columnDefs.map(
            item => item.headerName
        );

        expect(columnHeaders).toEqual(['Dimension', '#', 'Min / Max']);
    });

    it('should be correctly initialized for grid bid range popover', () => {
        const showCountColumn = false;
        const selectableRows = true;
        const selectionTooltip = 'Tooltip message';

        store.updateGridConfig(
            showCountColumn,
            selectableRows,
            selectionTooltip
        );
        expect(store.state.showCountColumn).toEqual(showCountColumn);
        expect(store.state.selectableRows).toEqual(selectableRows);
        expect(store.state.selectionTooltip).toEqual(selectionTooltip);
        expect(store.state.gridOptions).toEqual({
            suppressMovableColumns: true,
        } as GridOptions);

        const columnHeaders = store.state.columnDefs.map(
            item => item.headerName
        );

        expect(columnHeaders).toEqual(['', 'Dimension', 'Min / Max']);
        expect(
            store.state.columnDefs[0].headerComponentParams.popoverTooltip
        ).toEqual('Tooltip message');
    });

    it('should update type summary grid rows if they changed', () => {
        const typeSummaryGridRowsInitial = [
            {type: 'Device', count: 3, limits: {min: 0.8, max: 1.2}},
        ];
        const typeSummaryGridRowsFinal = [
            {type: 'Device', count: 3, limits: {min: 0.7, max: 1.1}},
        ];

        store.updateTypeSummaryGridRows(typeSummaryGridRowsInitial);

        spyOn(store, 'setState');

        store.updateTypeSummaryGridRows(typeSummaryGridRowsFinal);

        expect(store.setState).toHaveBeenCalledTimes(1);
    });

    it('should not update type summary grid rows if they did not change', () => {
        const typeSummaryGridRows = [
            {type: 'Device', count: 3, limits: {min: 0.8, max: 1.2}},
        ];

        store.updateTypeSummaryGridRows(typeSummaryGridRows);

        spyOn(store, 'setState');

        store.updateTypeSummaryGridRows(typeSummaryGridRows);

        expect(store.setState).toHaveBeenCalledTimes(0);
    });
});
