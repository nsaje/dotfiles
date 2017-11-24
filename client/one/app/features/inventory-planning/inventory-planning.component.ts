import './inventory-planning.component.less';

import {
    Component, Input, Output, EventEmitter, OnInit, OnDestroy, Inject, ChangeDetectionStrategy
} from '@angular/core';
import {Subject} from 'rxjs/Subject';
import 'rxjs/add/operator/takeUntil';
import 'rxjs/add/operator/distinctUntilChanged';

import {InventoryPlanningStore} from './inventory-planning.store';
import {InventoryPlanningEndpoint} from './inventory-planning.endpoint';
import {Filters} from './types/filters';

@Component({
    selector: 'zem-inventory-planning',
    templateUrl: './inventory-planning.component.html',
    providers: [InventoryPlanningStore, InventoryPlanningEndpoint],
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class InventoryPlanningComponent implements OnInit, OnDestroy {
    @Input() preselectedFilters?: {key: string, value: string}[];
    @Output() onSelectedFiltersUpdate = new EventEmitter<Filters>();

    private ngUnsubscribe$: Subject<undefined> = new Subject();

    constructor (private store: InventoryPlanningStore, @Inject('zemPermissions') private zemPermissions: any) {}  // tslint:disable-line no-unused-variable max-line-length

    ngOnInit () {
        if (this.preselectedFilters) {
            this.store.initWithPreselectedFilters(this.preselectedFilters);
        } else {
            this.store.init();
        }

        this.store.state$
            .takeUntil(this.ngUnsubscribe$)
            .map(state => state.selectedFilters)
            .distinctUntilChanged()
            .subscribe(selectedFilters => {
                this.onSelectedFiltersUpdate.emit(selectedFilters);
            });
    }

    ngOnDestroy () {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }
}
