import './inventory-planning-breakdown.component.less';

import {
    Component, Input, OnInit, OnChanges, OnDestroy, ChangeDetectionStrategy, ChangeDetectorRef
} from '@angular/core';
import {Subscription} from 'rxjs/Subscription';
import {Subject} from 'rxjs/Subject';
import 'rxjs/add/operator/debounceTime';
import 'rxjs/add/operator/distinctUntilChanged';

import {FilterOption} from '../types/filter-option';

const SEARCH_DEBOUNCE_TIME = 500;
const RENDERED_SEARCH_RESULTS_COUNT = 100;

@Component({
    selector: 'zem-inventory-planning-breakdown',
    templateUrl: './inventory-planning-breakdown.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class InventoryPlanningBreakdownComponent implements OnInit, OnChanges, OnDestroy {
    @Input() breakdownName: string;
    @Input() options: FilterOption[];
    @Input() isLoading: boolean;

    searchQuery: string = '';
    searchResults: FilterOption[] = [];
    search$: Subject<string> = new Subject<string>();

    private searchSubscription: Subscription;

    constructor (private changeDetectorRef: ChangeDetectorRef) {}

    ngOnInit () {
        this.searchSubscription = this.search$
            .debounceTime(SEARCH_DEBOUNCE_TIME)
            .distinctUntilChanged()
            .subscribe(searchQuery => {
                this.searchResults = this.search(searchQuery);
                this.changeDetectorRef.detectChanges();
            });
    }

    ngOnChanges (changes: any) {
        if (changes.options) {
            this.searchResults = this.search(this.searchQuery);
        }
    }

    ngOnDestroy () {
        this.searchSubscription.unsubscribe();
    }

    trackByOption (index: number, option: FilterOption): string {
        return option ? option.value : null;
    }

    private search (searchQuery?: string): FilterOption[] {
        let allSearchResults: FilterOption[] = [];
        this.searchQuery = searchQuery;

        if (!searchQuery || searchQuery === '') {
            allSearchResults = this.options;
        } else {
            searchQuery = searchQuery.toLowerCase();
            allSearchResults = this.options.filter(option => {
                const optionName = option.name || option.value || '';
                return optionName.toLowerCase().indexOf(searchQuery) !== -1;
            });
        }

        return allSearchResults.slice(0, RENDERED_SEARCH_RESULTS_COUNT);
    }
}
