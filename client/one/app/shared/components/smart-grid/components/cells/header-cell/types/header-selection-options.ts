import {HeaderParams} from './header-params';

export interface HeaderSelectionOptions {
    isDisabled: (params: HeaderParams) => boolean;
    isChecked: (params: HeaderParams) => boolean;
    setChecked?: (value: boolean, params: HeaderParams) => void;
}
