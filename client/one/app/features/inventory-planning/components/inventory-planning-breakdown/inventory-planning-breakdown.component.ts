import './inventory-planning-breakdown.component.less';

import {
    Component,
    Input,
    Output,
    EventEmitter,
    OnInit,
    OnChanges,
    OnDestroy,
    ChangeDetectionStrategy,
    ChangeDetectorRef,
    SimpleChanges,
} from '@angular/core';
import {Subscription, Subject} from 'rxjs';
import {debounceTime, distinctUntilChanged} from 'rxjs/operators';

import {FilterOption} from '../../types/filter-option';

const SEARCH_DEBOUNCE_TIME = 500;
const RENDERED_SEARCH_RESULTS_COUNT = 100;

@Component({
    selector: 'zem-inventory-planning-breakdown',
    templateUrl: './inventory-planning-breakdown.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class InventoryPlanningBreakdownComponent
    implements OnInit, OnChanges, OnDestroy {
    @Input()
    breakdownName: string;
    @Input()
    options: FilterOption[];
    @Input()
    selected: FilterOption[];
    @Input()
    isLoading: boolean;
    @Output()
    onToggle = new EventEmitter<string>();

    searchQuery: string = '';
    searchResults: FilterOption[] = [];
    search$: Subject<string> = new Subject<string>();
    selectedIndices: number[] = [];

    private searchSubscription: Subscription;

    constructor(private changeDetectorRef: ChangeDetectorRef) {}

    ngOnInit() {
        this.searchSubscription = this.search$
            .pipe(debounceTime(SEARCH_DEBOUNCE_TIME), distinctUntilChanged())
            .subscribe(searchQuery => {
                this.searchResults = this.search(searchQuery);
                this.selectedIndices = this.getSelectedIndices(
                    this.searchResults,
                    this.selected
                );
                this.changeDetectorRef.detectChanges();
            });
    }

    ngOnChanges(changes: SimpleChanges) {
        if (changes.options) {
            this.searchResults = this.search(this.searchQuery);
            this.selectedIndices = this.getSelectedIndices(
                this.searchResults,
                this.selected
            );
        }

        if (changes.selected) {
            this.selectedIndices = this.getSelectedIndices(
                this.searchResults,
                this.selected
            );
        }
    }

    ngOnDestroy() {
        this.searchSubscription.unsubscribe();
    }

    toggle(value: string) {
        this.onToggle.emit(value);
    }

    trackByOption(index: number, option: FilterOption): string {
        return option ? option.value : null;
    }

    private search(searchQuery?: string): FilterOption[] {
        let allSearchResults: FilterOption[] = [];
        this.searchQuery = searchQuery;

        if (!searchQuery || searchQuery === '') {
            allSearchResults = this.options.filter(
                option => option.auctionCount > 0
            );
        } else {
            searchQuery = searchQuery.toLowerCase();
            allSearchResults = this.options.filter(option => {
                const optionName = option.name || option.value || '';
                return (
                    option.auctionCount > 0 &&
                    optionName.toLowerCase().indexOf(searchQuery) !== -1
                );
            });
        }

        return allSearchResults.slice(0, RENDERED_SEARCH_RESULTS_COUNT);
    }

    private getSelectedIndices(
        allOptions: FilterOption[],
        selectedOptions: FilterOption[]
    ): number[] {
        const selectedIndices: number[] = [];
        allOptions.forEach((option, index) => {
            for (const selectedOption of selectedOptions) {
                if (selectedOption.value === option.value) {
                    selectedIndices.push(index);
                    break;
                }
            }
        });
        return selectedIndices;
    }
}
