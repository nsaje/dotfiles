import {ICellRendererParams} from 'ag-grid-community';
import {LinkCellIcon} from '../link-cell.component.constants';

export interface LinkRendererParams<T> extends ICellRendererParams {
    data: T;
    getText: (params: LinkRendererParams<T>) => string;
    getLink: (params: LinkRendererParams<T>) => string;
    getLinkIcon?: (params: LinkRendererParams<T>) => LinkCellIcon;
}
