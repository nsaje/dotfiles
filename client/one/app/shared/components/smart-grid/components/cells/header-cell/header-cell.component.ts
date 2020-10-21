import './header-cell.component.less';

import {IHeaderAngularComp} from 'ag-grid-angular';
import {HeaderParams} from './types/header-params';
import {Component} from '@angular/core';
import * as commonHelpers from '../../../../../helpers/common.helpers';
import {
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

    sort: HeaderCellSort;
    initialSort: HeaderCellSort;
    sortingOrder: HeaderCellSort[];

    isChecked: boolean;
    isCheckboxDisabled: boolean;

    agInit(params: HeaderParams): void {
        this.params = {
            ...DEFAULT_HEADER_PARAMS,
            ...params,
        };
        this.colDef = this.params.column.getColDef();
        this.colId = this.params.column.getColId();
        this.field = this.colDef.field;

        if (this.params.enableSorting) {
            this.sort = this.params.sortOptions.sort;
            this.initialSort = this.params.sortOptions.initialSort;
            this.sortingOrder = commonHelpers.getValueOrDefault(
                this.params.sortOptions.sortingOrder,
                DEFAULT_HEADER_CELL_SORT_ORDER
            );
        }

        if (this.params.enableSelection) {
            this.isChecked = this.params.selectionOptions.isChecked(
                this.params
            );
            this.isCheckboxDisabled = this.params.selectionOptions.isDisabled(
                this.params
            );
        }
    }

    setChecked($event: boolean) {
        if (!this.params.enableSelection) {
            return;
        }
        this.params.selectionOptions.setChecked($event, this.params);
    }

    setSort(): void {
        if (!this.params.enableSorting) {
            return;
        }

        const futureSort = this.toggleSort(this.sort);
        switch (this.params.sortOptions.sortType) {
            case 'client':
                this.setClientSort(futureSort);
                break;
            case 'server':
                this.setServerSort(futureSort);
                break;
        }
    }

    private toggleSort(sort: HeaderCellSort): HeaderCellSort {
        switch (sort) {
            case this.sortingOrder[0]:
                return this.sortingOrder[1];
            case this.sortingOrder[1]:
                return this.sortingOrder[0];
            default:
                return commonHelpers.getValueOrDefault(
                    this.initialSort,
                    this.sortingOrder[0]
                );
        }
    }

    private setClientSort(sort: HeaderCellSort): void {
        const sortModel: SortModel[] = [{colId: this.colId, sort: sort}];
        this.params.api.setSortModel(sortModel);
    }

    private setServerSort(sort: HeaderCellSort): void {
        const sortField: string = commonHelpers.getValueOrDefault(
            this.params.sortOptions.orderField,
            this.field
        );
        const sortModel: SortModel[] = [{colId: sortField, sort: sort}];
        this.params.sortOptions.setSortModel(sortModel);
    }
}
