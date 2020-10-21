import {HeaderCellSort} from '../header-cell.component.constants';
import {SortModel} from './sort-models';

export interface HeaderSortOptions {
    sort?: HeaderCellSort;
    initialSort?: HeaderCellSort;
    sortingOrder?: HeaderCellSort[];
    orderField?: string;
    sortType?: 'client' | 'server';
    setSortModel?: (sortModel: SortModel[]) => void;
}
