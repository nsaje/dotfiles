import {HeaderCellSort} from './header-cell.component.constants';
import {HeaderParams} from './types/header-params';
import {HeaderSortOptions} from './types/header-sort-options';

export const DEFAULT_HEADER_CELL_SORT_ORDER: HeaderCellSort[] = [
    HeaderCellSort.DESC,
    HeaderCellSort.ASC,
];

export const DEFAULT_HEADER_CELL_SORT_OPTIONS: HeaderSortOptions = {
    sortType: 'client',
    initialSort: HeaderCellSort.DESC,
};

export const DEFAULT_HEADER_PARAMS: Partial<HeaderParams> = {
    internalFeature: false,
    enableSelection: false,
    enableSorting: false,
    sortOptions: DEFAULT_HEADER_CELL_SORT_OPTIONS,
};
