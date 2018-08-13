import './inventory-planning.view.less';

import {
    Component,
    OnInit,
    Inject,
    OnDestroy,
    ChangeDetectionStrategy,
    HostBinding,
} from '@angular/core';
import {downgradeComponent} from '@angular/upgrade/static';

import {Subject} from 'rxjs';
import {takeUntil, map, distinctUntilChanged} from 'rxjs/operators';

import {Filters} from '../../types/filters';
import {FilterOption} from '../../types/filter-option';
import {InventoryPlanningStore} from '../../services/inventory-planning.store';
import {InventoryPlanningEndpoint} from '../../services/inventory-planning.endpoint';

const FILTER_URL_PARAMS = ['countries', 'publishers', 'devices', 'sources'];

@Component({
    selector: 'zem-inventory-planning-view',
    templateUrl: './inventory-planning.view.html',
    providers: [InventoryPlanningStore, InventoryPlanningEndpoint],
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class InventoryPlanningView implements OnInit, OnDestroy {
    @HostBinding('class')
    cssClass = 'zem-inventory-planning-view';

    private ngUnsubscribe$: Subject<undefined> = new Subject();

    constructor(
        @Inject('ajs$location') private ajs$location: any,
        public store: InventoryPlanningStore
    ) {}

    ngOnInit() {
        const preselectedFilters = this.getPreselectedFiltersFromUrlParams();
        if (preselectedFilters) {
            this.store.initWithPreselectedFilters(preselectedFilters);
        } else {
            this.store.init();
        }

        this.store.state$
            .pipe(
                map(state => state.selectedFilters),
                distinctUntilChanged(),
                takeUntil(this.ngUnsubscribe$)
            )
            .subscribe(selectedFilters => {
                this.updateUrlParamsWithSelectedFilters(selectedFilters);
            });
    }

    ngOnDestroy(): void {
        this.store.destroy();
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    updateUrlParamsWithSelectedFilters(selectedFilters: Filters) {
        FILTER_URL_PARAMS.forEach(paramName => {
            const paramValue = selectedFilters[paramName]
                .map((x: FilterOption) => x.value)
                .join(',');
            this.setUrlParam(paramName, paramValue);
        });
    }

    private getPreselectedFiltersFromUrlParams(): {
        key: string;
        value: string;
    }[] {
        const preselectedFilters: {key: string; value: string}[] = [];
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

    private setUrlParam(name: string, value: string) {
        if (!value) {
            value = null;
        }
        this.ajs$location.search(name, value).replace();
    }
}

declare var angular: angular.IAngularStatic;
angular
    .module('one.downgraded')
    .directive(
        'zemInventoryPlanningView',
        downgradeComponent({component: InventoryPlanningView})
    );
