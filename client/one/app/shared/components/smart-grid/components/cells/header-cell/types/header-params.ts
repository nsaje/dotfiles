import {IHeaderParams} from 'ag-grid-community';
import {PopoverPlacement} from '../../../../../popover/types/popover-placement';
import {CellRole} from '../../../../smart-grid.component.constants';
import {HeaderCellIcon} from '../header-cell.component.constants';
import {HeaderSelectionOptions} from './header-selection-options';
import {HeaderSortOptions} from './header-sort-options';

export interface HeaderParams extends IHeaderParams {
    internalFeature?: boolean;
    enableSorting: boolean;
    sortOptions?: HeaderSortOptions;
    enableSelection: boolean;
    selectionOptions?: HeaderSelectionOptions;
    popoverTooltip?: string;
    popoverPlacement?: PopoverPlacement;
    icon?: HeaderCellIcon;
    role?: CellRole;
}
