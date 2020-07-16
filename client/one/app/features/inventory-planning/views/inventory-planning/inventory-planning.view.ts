import './inventory-planning.view.less';

import {
    Component,
    OnInit,
    Inject,
    OnDestroy,
    ChangeDetectionStrategy,
    HostBinding,
} from '@angular/core';
import {Subject} from 'rxjs';
import {takeUntil, map, distinctUntilChanged} from 'rxjs/operators';
import {Router, ActivatedRoute} from '@angular/router';

import {Filters} from '../../types/filters';
import {FilterOption} from '../../types/filter-option';
import {InventoryPlanningStore} from '../../services/inventory-planning.store';
import {InventoryPlanningEndpoint} from '../../services/inventory-planning.endpoint';
import {PostAsGetRequestService} from '../../../../core/post-as-get-request/post-as-get-request.service';
import * as requestPayloadHelpers from '../../helpers/request-payload.helpers';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';

const FILTER_URL_PARAMS = [
    'countries',
    'publishers',
    'devices',
    'sources',
    'channels',
];

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
        public store: InventoryPlanningStore,
        private postAsGetRequestService: PostAsGetRequestService,
        private route: ActivatedRoute,
        private router: Router,
        @Inject('zemPermissions') public zemPermissions: any
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
        const queryParams = {};
        FILTER_URL_PARAMS.forEach(paramName => {
            const paramValue = selectedFilters[paramName]
                .map((x: FilterOption) => x.value)
                .join(',');
            if (paramValue !== '') {
                queryParams[paramName] = paramValue;
            }
        });
        this.router.navigate([], {
            relativeTo: this.route,
            queryParams: queryParams,
            replaceUrl: true,
        });
    }

    exportInventoryData() {
        const filterPayload = requestPayloadHelpers.buildRequestPayload(
            this.store.state.selectedFilters
        );
        const url = '/rest/internal/inventory-planning/export';
        this.postAsGetRequestService.postAsGet(filterPayload, url);
    }

    private getPreselectedFiltersFromUrlParams(): {
        key: string;
        value: string;
    }[] {
        const preselectedFilters: {key: string; value: string}[] = [];
        FILTER_URL_PARAMS.forEach(paramName => {
            const values: string = this.route.snapshot.queryParamMap.get(
                paramName
            );
            if (values) {
                values.split(',').forEach(value => {
                    preselectedFilters.push({key: paramName, value: value});
                });
            }
        });
        return preselectedFilters.length > 0 ? preselectedFilters : null;
    }
}
