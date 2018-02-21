import {Injectable} from '@angular/core';

import {Store} from '../../shared/types/store';
import {InventoryPlanningState} from './inventory-planning-state';
import {InventoryPlanningEndpoint} from './inventory-planning.endpoint';
import {Requests} from './types/requests';
import {Inventory} from './types/inventory';
import {Filters} from './types/filters';
import {FilterOption} from './types/filter-option';

@Injectable()
export class InventoryPlanningStore extends Store<InventoryPlanningState> {
    private preselectedFilterOptions: {key: string, value: string}[];

    constructor (private endpoint: InventoryPlanningEndpoint) {
        super(new InventoryPlanningState());
    }

    init (): void {
        this.refreshData(this.state.selectedFilters);
    }

    initWithPreselectedFilters (preselectedOptions: {key: string, value: string}[]): void {
        // Add placeholder selected filters in order to make a filtered first request to REST API
        const placeholderSelectedFilters: Filters = {
            countries: [],
            publishers: [],
            devices: [],
            sources: [],
        };
        preselectedOptions.forEach(preselectedOption => {
            if (!placeholderSelectedFilters.hasOwnProperty(preselectedOption.key)) {
                return;
            }
            placeholderSelectedFilters[preselectedOption.key] = [
                ...placeholderSelectedFilters[preselectedOption.key],
                {name: '', value: preselectedOption.value, auctionCount: -1},
            ];
        });

        // Save preselected filter options to replace them with actual data from available filters after they have been
        // loaded
        this.preselectedFilterOptions = preselectedOptions;

        // Refresh data from REST API with preselected filters applied
        this.refreshData(placeholderSelectedFilters);
    }

    toggleOption (toggledOption: {key: string, value: string}): void {
        if (!this.state.selectedFilters.hasOwnProperty(toggledOption.key)) {
            return;
        }
        this.setState({
            ...this.state,
            selectedFilters: {
                ...this.state.selectedFilters,
                [toggledOption.key]: this.getSelectedWithToggledOption(
                    this.state.availableFilters[toggledOption.key],
                    this.state.selectedFilters[toggledOption.key],
                    toggledOption.value
                ),
            },
        });
        this.refreshData(this.state.selectedFilters);
    }

    applyFilters (appliedOptions: {key: string, value: string}[]): void {
        this.setSelectedFilters(appliedOptions);
        this.refreshData(this.state.selectedFilters);
    }

    private refreshData (selectedFilters: Filters): void {
        const requests: Requests = {
            summary: {
                inProgress: true,
            },
            countries: {
                inProgress: true,
            },
            publishers: {
                inProgress: true,
            },
            devices: {
                inProgress: true,
            },
            sources: {
                inProgress: true,
            },
        };

        if (this.state.requests.summary.subscription) {
            this.state.requests.summary.subscription.unsubscribe();
        }
        requests.summary.subscription = this.endpoint
            .loadSummary(selectedFilters)
            .subscribe(this.handleLoadSummaryResponse.bind(this));

        if (this.state.requests.countries.subscription) {
            this.state.requests.countries.subscription.unsubscribe();
        }
        requests.countries.subscription = this.endpoint
            .loadCountries(selectedFilters)
            .subscribe(breakdown => { this.handleBreakdownResponse('countries', breakdown); });

        if (this.state.requests.publishers.subscription) {
            this.state.requests.publishers.subscription.unsubscribe();
        }
        requests.publishers.subscription = this.endpoint
            .loadPublishers(selectedFilters)
            .subscribe(breakdown => { this.handleBreakdownResponse('publishers', breakdown); });

        if (this.state.requests.devices.subscription) {
            this.state.requests.devices.subscription.unsubscribe();
        }
        requests.devices.subscription = this.endpoint
            .loadDevices(selectedFilters)
            .subscribe(breakdown => { this.handleBreakdownResponse('devices', breakdown); });

        if (this.state.requests.sources.subscription) {
            this.state.requests.sources.subscription.unsubscribe();
        }
        requests.sources.subscription = this.endpoint
            .loadSources(selectedFilters)
            .subscribe(breakdown => { this.handleBreakdownResponse('sources', breakdown); });

        this.setState({
            ...this.state,
            requests: requests,
        });
    }

    private handleLoadSummaryResponse (inventory: Inventory): void {
        this.setState({
            ...this.state,
            inventory: inventory,
            requests: {
                ...this.state.requests,
                summary: {
                    ...this.state.requests.summary,
                    subscription: null,
                    inProgress: false,
                },
            },
        });
    }

    private handleBreakdownResponse (key: string, breakdown: FilterOption[]): void {
        this.setState({
            ...this.state,
            availableFilters: {
                ...this.state.availableFilters,
                [key]: breakdown,
            },
            requests: {
                ...this.state.requests,
                [key]: {
                    ...this.state.requests[key],
                    subscription: null,
                    inProgress: false,
                },
            },
        });

        // Replace placeholder selected filters with actual data from available filters
        if (this.preselectedFilterOptions) {
            this.replacePlaceholderFilterOptions();
        }
    }

    private setSelectedFilters (selectedOptions: {key: string, value: string}[]): void {
        const selectedFilters: Filters = {
            countries: [],
            publishers: [],
            devices: [],
            sources: [],
        };

        selectedOptions.forEach(selectedOption => {
            if (!selectedFilters.hasOwnProperty(selectedOption.key)) {
                return;
            }
            const filterOption = this.getFilterOption(selectedOption.key, selectedOption.value);
            if (filterOption) {
                selectedFilters[selectedOption.key] = [
                    ...selectedFilters[selectedOption.key],
                    filterOption,
                ];
            }
        });

        this.setState({
            ...this.state,
            selectedFilters: selectedFilters,
        });
    }

    private getSelectedWithToggledOption (
        available: FilterOption[],
        selected: FilterOption[],
        value: string
    ): FilterOption[] {
        const selectedWithNoToggledOption = selected.filter(i => i.value !== value);
        if (selectedWithNoToggledOption.length === selected.length) {
            for (const filter of available) {
                if (filter.value === value) {
                    return [
                        ...selectedWithNoToggledOption,
                        filter,
                    ];
                }
            }
        }
        return selectedWithNoToggledOption;
    }

    private getFilterOption (key: string, value: string): FilterOption {
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

    private replacePlaceholderFilterOptions (): void {
        this.setSelectedFilters(this.preselectedFilterOptions);

        const isAnyAvailableFiltersCategoryEmpty = Object.keys(this.state.availableFilters)
            .some(key => this.state.availableFilters[key].length === 0 && this.state.requests[key].inProgress);
        if (!isAnyAvailableFiltersCategoryEmpty) {
            this.preselectedFilterOptions = null;
        }
    }
}
