import {ICellRendererParams} from 'ag-grid-community';

export interface NoteRendererParams<T> extends ICellRendererParams {
    data: T;
    getMainContent: (item: T) => string;
    getNote: (item: T) => string;
}
