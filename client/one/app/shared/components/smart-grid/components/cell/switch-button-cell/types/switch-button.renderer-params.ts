import {ICellRendererParams} from 'ag-grid-community';

export interface SwitchButtonRendererParams<T, S> extends ICellRendererParams {
    data: T;
    context: {componentParent: S};
    getSwitchValue: (item: T) => boolean;
    toggle: (componentParent: S, item: T, value: boolean) => void;
    isReadOnly: (componentParent: S, item: T) => boolean;
}
