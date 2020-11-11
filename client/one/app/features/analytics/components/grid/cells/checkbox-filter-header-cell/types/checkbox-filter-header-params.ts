import {IHeaderParams} from 'ag-grid-community';
import {GridSelectionCustomFilter} from '../../../grid-bridge/types/grid-selection-custom-filter';

export interface CheckboxFilterHeaderParams extends IHeaderParams {
    isChecked: (params: CheckboxFilterHeaderParams) => boolean;
    setChecked?: (value: boolean, params: CheckboxFilterHeaderParams) => void;
    getCustomFilters: (
        params: CheckboxFilterHeaderParams
    ) => GridSelectionCustomFilter[];
    setCustomFilter?: (
        value: GridSelectionCustomFilter,
        params: CheckboxFilterHeaderParams
    ) => void;
}
