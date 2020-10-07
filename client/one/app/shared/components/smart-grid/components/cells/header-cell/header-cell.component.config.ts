import {HeaderCellSort} from './header-cell.component.constants';
import {HeaderSortOptions} from './types/header-sort-options';

export const DEFAULT_HEADER_CELL_SORT_ORDER: HeaderCellSort[] = [
    HeaderCellSort.DESC,
    HeaderCellSort.ASC,
];

export const DEFAULT_HEADER_CELL_SORT_OPTIONS: HeaderSortOptions = {
    sortType: 'client',
    initialSort: HeaderCellSort.DESC,
};
