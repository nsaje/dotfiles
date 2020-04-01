import {IHeaderParams} from 'ag-grid-community';

export interface HelpPopoverHeaderParams extends IHeaderParams {
    tooltip: string;
    popoverPlacement: string;
}
