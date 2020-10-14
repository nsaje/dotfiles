import './header-cell.component.less';

import {IHeaderAngularComp} from 'ag-grid-angular';
import {HeaderParams} from './types/header-params';
import {Component} from '@angular/core';
import * as commonHelpers from '../../../../../helpers/common.helpers';
import {
    DEFAULT_HEADER_CELL_SORT_OPTIONS,
    DEFAULT_HEADER_CELL_SORT_ORDER,
    DEFAULT_HEADER_PARAMS,
} from './header-cell.component.config';
import {SortModel} from './types/sort-models';
import {HeaderCellSort} from './header-cell.component.constants';
import {ColDef} from 'ag-grid-community';

@Component({
    templateUrl: './header-cell.component.html',
})
export class HeaderCellComponent implements IHeaderAngularComp {
    params: HeaderParams;

    HeaderCellSort = HeaderCellSort;

    colDef: ColDef;
    colId: string;
    field: string;
    sort: string;
    sortingOrder: string[];

    agInit(params: HeaderParams): void {
        this.params = {
            ...DEFAULT_HEADER_PARAMS,
            ...params,
        };
        this.colDef = this.params.column.getColDef();
        this.colId = this.params.column.getColId();
        this.field = this.colDef.field;
        this.sort = this.colDef.sort;
        this.sortingOrder = commonHelpers.getValueOrDefault(
            this.colDef.sortingOrder,
            DEFAULT_HEADER_CELL_SORT_ORDER
        );
    }

    setSort(): void {
        if (!this.params.enableSorting) {
            return;
        }

        this.sort = this.toggleSort(this.sort);
        switch (this.params.sortOptions.sortType) {
            case 'client':
                this.setClientSort(this.sort);
                break;
            case 'server':
                this.setServerSort(this.sort);
                break;
        }
    }

    private toggleSort(sort: string): string {
        switch (sort) {
            case this.sortingOrder[0]:
                return this.sortingOrder[1];
            case this.sortingOrder[1]:
                return this.sortingOrder[0];
            default:
                return commonHelpers.getValueOrDefault(
                    this.params.sortOptions.initialSort,
                    this.sortingOrder[0]
                );
        }
    }

    private setClientSort(sort: string): void {
        const sortModel: SortModel[] = [{colId: this.colId, sort: sort}];
        this.params.api.setSortModel(sortModel);
    }

    private setServerSort(sort: string): void {
        const sortField: string = commonHelpers.getValueOrDefault(
            this.params.sortOptions.orderField,
            this.field
        );
        const sortModel: SortModel[] = [{colId: sortField, sort: sort}];
        this.params.sortOptions.setSortModel(sortModel);
    }
}
