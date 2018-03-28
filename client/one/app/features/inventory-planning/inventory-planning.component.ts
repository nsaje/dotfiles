import './inventory-planning.component.less';

import {
    Component, Input, Output, EventEmitter, OnInit, OnDestroy, ChangeDetectionStrategy
} from '@angular/core';
import {Subject} from 'rxjs/Subject';
import {map, takeUntil, distinctUntilChanged} from 'rxjs/operators';

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

    constructor (private store: InventoryPlanningStore) {}

    ngOnInit () {
        if (this.preselectedFilters) {
            this.store.initWithPreselectedFilters(this.preselectedFilters);
        } else {
            this.store.init();
        }

        this.store.state$
            .pipe(
                takeUntil(this.ngUnsubscribe$),
                map(state => state.selectedFilters),
                distinctUntilChanged()
            )
            .subscribe(selectedFilters => {
                this.onSelectedFiltersUpdate.emit(selectedFilters);
            });
    }

    ngOnDestroy () {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }
}
