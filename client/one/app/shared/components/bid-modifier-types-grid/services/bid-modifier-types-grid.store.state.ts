import {SmartGridColDef} from '../../../../shared/components/smart-grid/types/smart-grid-col-def';
import {GridOptions} from 'ag-grid-community';
import {TypeSummaryGridRow} from './type-summary-grid-row';

export class BidModifierTypesGridStoreState {
    showCountColumn: boolean = true;
    selectableRows: boolean = false;
    selectionTooltip: string = null;
    gridOptions: GridOptions = null;
    columnDefs: SmartGridColDef[] = null;
    typeSummaryGridRows: TypeSummaryGridRow[] = null;
}
