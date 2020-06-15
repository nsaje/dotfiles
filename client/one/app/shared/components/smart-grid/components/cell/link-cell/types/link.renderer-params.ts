import {ICellRendererParams} from 'ag-grid-community';

export interface LinkRendererParams<T> extends ICellRendererParams {
    data: T;
    getText: (item: T) => string;
    getLink: (item: T) => string;
}
