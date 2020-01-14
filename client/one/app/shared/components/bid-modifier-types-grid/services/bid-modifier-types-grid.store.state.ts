import {ColDef, GridOptions} from 'ag-grid-community';
import {TypeSummaryGridRow} from './type-summary-grid-row';

export class BidModifierTypesGridStoreState {
    showCountColumn: boolean = true;
    selectableRows: boolean = false;
    selectionTooltip: string = null;
    gridOptions: GridOptions = null;
    columnDefs: ColDef[] = null;
    typeSummaryGridRows: TypeSummaryGridRow[] = null;
}
