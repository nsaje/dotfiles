import {IHeaderParams} from 'ag-grid-community';
import {PopoverPlacement} from '../../../../../popover/types/popover-placement';
import {HeaderCellIcon} from '../header-cell.component.constants';
import {HeaderSortOptions} from './header-sort-options';

export interface HeaderParams extends IHeaderParams {
    internalFeature?: boolean;
    sortOptions?: HeaderSortOptions;
    popoverTooltip?: string;
    popoverPlacement?: PopoverPlacement;
    icon?: HeaderCellIcon;
}
