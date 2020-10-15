import {ICellRendererParams} from 'ag-grid-community';

export interface CheckboxRendererParams extends ICellRendererParams {
    isDisabled: (params: CheckboxRendererParams) => boolean;
    isChecked: (params: CheckboxRendererParams) => boolean;
    setChecked?: (value: boolean, params: CheckboxRendererParams) => void;
}
