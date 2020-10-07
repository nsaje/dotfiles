import {HeaderCellSort} from '../header-cell.component.constants';
import {SortModel} from './sort-models';

export interface HeaderSortOptions {
    initialSort?: HeaderCellSort;
    sortType?: 'client' | 'server';
    setSortModel?: (sortModel: SortModel[]) => void;
}
