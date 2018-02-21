import {Component, OnInit, Inject} from '@angular/core';
import {downgradeComponent} from '@angular/upgrade/static';

import {Filters} from '../../features/inventory-planning/types/filters';
import {FilterOption} from '../../features/inventory-planning/types/filter-option';

const FILTER_URL_PARAMS = ['countries', 'publishers', 'devices', 'sources'];

@Component({
    selector: 'zem-inventory-planning-view',
    templateUrl: './inventory-planning.view.html',
})
export class InventoryPlanningViewComponent implements OnInit {
    preselectedFilters: {key: string, value: string}[];

    constructor (@Inject('ajs$location') private ajs$location: any) {}

    ngOnInit () {
        this.preselectedFilters = this.getPreselectedFiltersFromUrlParams();
    }

    updateUrlParamsWithSelectedFilters (selectedFilters: Filters) {
        FILTER_URL_PARAMS.forEach(paramName => {
            this.setUrlParam(paramName, selectedFilters[paramName].map((x: FilterOption) => x.value).join(','));
        });
    }

    private getPreselectedFiltersFromUrlParams (): {key: string, value: string}[] {
        const preselectedFilters: {key: string, value: string}[] = [];
        FILTER_URL_PARAMS.forEach(paramName => {
            const values: string = this.ajs$location.search()[paramName];
            if (values) {
                values.split(',').forEach(value => {
                    preselectedFilters.push({key: paramName, value: value});
                });
            }
        });
        return preselectedFilters.length > 0 ? preselectedFilters : null;
    }

    private setUrlParam (name: string, value: string) {
        if (!value) {
            value = null;
        }
        this.ajs$location.search(name, value).replace();
    }
}

declare var angular: angular.IAngularStatic;
angular.module('one.downgraded').directive(
    'zemInventoryPlanningView',
    downgradeComponent({component: InventoryPlanningViewComponent}) as angular.IDirectiveFactory
);
