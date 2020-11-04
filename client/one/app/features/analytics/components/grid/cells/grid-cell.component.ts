import {ICellRendererParams} from 'ag-grid-community';
import {GridRow} from '../grid-bridge/types/grid-row';

export abstract class GridCellComponent {
    getElement(selectors: string): HTMLElement {
        const containerElements = document.querySelectorAll(selectors);
        return Array.from(containerElements).find(element => {
            const domRect: DOMRect = element.getBoundingClientRect();
            return domRect.width > 0 && domRect.height > 0;
        }) as HTMLElement;
    }

    flashCell(params: ICellRendererParams) {
        setTimeout(() => {
            const colId = params.column.getColDef().colId;
            const rowNode = params.api.getRowNode((params.data as GridRow).id);
            params.api.flashCells({
                columns: [colId],
                rowNodes: [rowNode],
            });
        });
    }
}
