import {ICellRendererParams} from 'ag-grid-community';

export interface SwitchButtonRendererParams extends ICellRendererParams {
    isDisabled: (params: SwitchButtonRendererParams) => boolean;
    isSwitchedOn: (params: SwitchButtonRendererParams) => boolean;
    toggle?: (value: boolean, params: SwitchButtonRendererParams) => void;
}
