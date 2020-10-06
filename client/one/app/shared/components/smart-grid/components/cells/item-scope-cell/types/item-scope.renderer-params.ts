import {ICellRendererParams} from 'ag-grid-community';

export interface ItemScopeRendererParams<T> extends ICellRendererParams {
    data: T;
    agencyIdField?: string;
    agencyNameField?: string;
    canUseAgencyLink?: boolean;
    accountIdField?: string;
    accountNameField?: string;
    canUseAccountLink?: boolean;
    getAgencyLink?(item: T): string;
    getAccountLink?(item: T): string;
}
