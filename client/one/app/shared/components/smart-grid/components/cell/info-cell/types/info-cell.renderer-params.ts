import {ICellRendererParams} from 'ag-grid-community';

export interface InfoCellRendererParams<T, S> extends ICellRendererParams {
    data: T;
    context: {componentParent: S};
    getMainContent: (item: T, componentParent?: S) => string;
    getInfoText: (item: T, componentParent?: S) => string;
}
