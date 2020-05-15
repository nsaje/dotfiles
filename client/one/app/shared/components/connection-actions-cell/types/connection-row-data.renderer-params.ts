import {ICellRendererParams} from 'ag-grid-community';
import {ConnectionRowParentComponent} from './connection-row-parent-component';

export interface ConnectionRowDataRendererParams<
    T,
    S extends ConnectionRowParentComponent<T>
> extends ICellRendererParams {
    context: {
        componentParent: S;
    };
    data: T;
}
