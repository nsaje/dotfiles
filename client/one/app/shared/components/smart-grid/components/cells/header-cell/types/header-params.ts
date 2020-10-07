import {IHeaderParams} from 'ag-grid-community';
import {PopoverPlacement} from '../../../../../popover/types/popover-placement';
import {HeaderSortOptions} from './header-sort-options';

export interface HeaderParams extends IHeaderParams {
    sortOptions?: HeaderSortOptions;
    popoverTooltip?: string;
    popoverPlacement?: PopoverPlacement;
}
