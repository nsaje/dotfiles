import {Injectable} from '@angular/core';

import {Subject, Observable, forkJoin} from 'rxjs';
import {
    takeUntil,
    distinctUntilChanged,
    tap,
    switchMap,
    retry,
} from 'rxjs/operators';
import {Store} from 'rxjs-observable-store';

import {InventoryPlanningState} from './inventory-planning.state';
import {InventoryPlanningEndpoint} from './inventory-planning.endpoint';
import {Filters} from '../types/filters';
import {Inventory} from '../types/inventory';
import {FilterOption} from '../types/filter-option';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import * as storeHelpers from '../../../shared/helpers/store.helpers';

@Injectable()
export class InventoryPlanningStore extends Store<InventoryPlanningState> {
    private ngUnsubscribe$: Subject<undefined> = new Subject();
    private filters$: Subject<Filters> = new Subject();
    private requestStateUpdater: RequestStateUpdater;

    constructor(private endpoint: InventoryPlanningEndpoint) {
        super(new InventoryPlanningState());

        this.requestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this
        );
    }

    init(): void {
        const filters: Filters = {
            countries: [],
            publishers: [],
            devices: [],
            sources: [],
        };

        this.subscribeToFiltersUpdates();
        this.filters$.next(filters);
    }

    initWithPreselectedFilters(
        preselectedOptions: {key: string; value: string}[]
    ): void {
        const filters: Filters = {
            countries: [],
            publishers: [],
            devices: [],
            sources: [],
        };

        preselectedOptions.forEach(option => {
            if (!filters.hasOwnProperty(option.key)) {
                return;
            }
            filters[option.key] = [
                ...filters[option.key],
                {name: '', value: option.value, auctionCount: -1},
            ];
        });

        this.subscribeToFiltersUpdates();
        this.filters$.next(filters);
    }

    destroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    applyFilters(options: {key: string; value: string}[]): void {
        const filters: Filters = {
            countries: [],
            publishers: [],
            devices: [],
            sources: [],
        };

        options.forEach(option => {
            if (!filters.hasOwnProperty(option.key)) {
                return;
            }

            const filterOption = this.getFilterOption(option.key, option.value);
            if (filterOption) {
                filters[option.key] = [...filters[option.key], filterOption];
            }
        });

        this.filters$.next(filters);
    }

    toggleOption(option: {key: string; value: string}): void {
        if (!this.state.selectedFilters.hasOwnProperty(option.key)) {
            return;
        }

        const filters = {
            ...this.state.selectedFilters,
            [option.key]: this.getSelectedWithToggledOption(
                this.state.availableFilters[option.key],
                this.state.selectedFilters[option.key],
                option.value
            ),
        };

        this.filters$.next(filters);
    }

    private subscribeToFiltersUpdates(): void {
        this.filters$
            .pipe(
                distinctUntilChanged(),
                tap(filters => {
                    this.setState({
                        ...this.state,
                        selectedFilters: filters,
                    });
                }),
                switchMap(filters => {
                    const summaryObservable = this.reloadSummary(filters);
                    const countriesObservable = this.reloadCountries(filters);
                    const publishersObservable = this.reloadPublishers(filters);
                    const devicesObservable = this.reloadDevices(filters);
                    const sourcesObservable = this.reloadSources(filters);

                    // forkJoin: When all observables complete, emit the last emitted value from each.
                    // https://www.learnrxjs.io/operators/combination/forkjoin.html
                    return forkJoin(
                        summaryObservable,
                        countriesObservable,
                        publishersObservable,
                        devicesObservable,
                        sourcesObservable
                    );
                }),
                retry(),
                takeUntil(this.ngUnsubscribe$)
            )
            .subscribe();
    }

    private reloadSummary(filters: Filters): Observable<Inventory> {
        return this.endpoint
            .loadSummary(filters, this.requestStateUpdater)
            .pipe(
                tap((response: any) => {
                    this.handleSummaryResponse(response);
                })
            );
    }

    private reloadCountries(filters: Filters): Observable<FilterOption[]> {
        return this.endpoint
            .loadCountries(filters, this.requestStateUpdater)
            .pipe(
                tap((response: any) => {
                    this.handleBreakdownResponse('countries', response);
                })
            );
    }

    private reloadPublishers(filters: Filters): Observable<FilterOption[]> {
        return this.endpoint
            .loadPublishers(filters, this.requestStateUpdater)
            .pipe(
                tap((response: any) => {
                    this.handleBreakdownResponse('publishers', response);
                })
            );
    }

    private reloadDevices(filters: Filters): Observable<FilterOption[]> {
        return this.endpoint
            .loadDevices(filters, this.requestStateUpdater)
            .pipe(
                tap((response: any) => {
                    this.handleBreakdownResponse('devices', response);
                })
            );
    }

    private reloadSources(filters: Filters): Observable<FilterOption[]> {
        return this.endpoint
            .loadSources(filters, this.requestStateUpdater)
            .pipe(
                tap((response: any) => {
                    this.handleBreakdownResponse('sources', response);
                })
            );
    }

    private handleSummaryResponse(response: Inventory): void {
        this.setState({
            ...this.state,
            inventory: response,
        });
    }

    private handleBreakdownResponse(
        key: string,
        response: FilterOption[]
    ): void {
        this.setState({
            ...this.state,
            availableFilters: {
                ...this.state.availableFilters,
                [key]: response,
            },
        });
    }

    private getSelectedWithToggledOption(
        available: FilterOption[],
        selected: FilterOption[],
        value: string
    ): FilterOption[] {
        const selectedWithNoToggledOption = selected.filter(
            i => i.value !== value
        );
        if (selectedWithNoToggledOption.length === selected.length) {
            for (const filter of available) {
                if (filter.value === value) {
                    return [...selectedWithNoToggledOption, filter];
                }
            }
        }
        return selectedWithNoToggledOption;
    }

    private getFilterOption(key: string, value: string): FilterOption {
        if (!this.state.availableFilters.hasOwnProperty(key)) {
            return null;
        }

        for (const option of this.state.availableFilters[key]) {
            if (option.value === value) {
                return option;
            }
        }
        return null;
    }
}
