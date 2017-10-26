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
    constructor (private endpoint: InventoryPlanningEndpoint) {
        super(new InventoryPlanningState());

        this.refreshData(this.state.selectedFilters);
    }

    private refreshData (selectedFilters: Filters) {
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

        this.setState({
            ...this.state,
            requests: requests,
        });
    }

    removeOption ($event: {key: string, value: string}): void {
        if (!this.state.selectedFilters.hasOwnProperty($event.key)) {
            return;
        }
        const selectedWithRemovedOption = this.state.selectedFilters[$event.key].filter((option: FilterOption) => {
            return option.value !== $event.value;
        });
        this.setState({
            ...this.state,
            selectedFilters: {
                ...this.state.selectedFilters,
                [$event.key]: selectedWithRemovedOption,
            },
        });
        this.refreshData(this.state.selectedFilters);
    }

    applyFilters ($event: {key: string, value: string}[]): void {
        const selectedFilters: Filters = {
            countries: [],
            publishers: [],
            devices: [],
        };

        $event.forEach(appliedOption => {
            if (!selectedFilters.hasOwnProperty(appliedOption.key)) {
                return;
            }
            selectedFilters[appliedOption.key] = [
                ...selectedFilters[appliedOption.key],
                this.getFilterOption(appliedOption.key, appliedOption.value),
            ];
        });
        this.setState({
            ...this.state,
            selectedFilters: selectedFilters,
        });
        this.refreshData(this.state.selectedFilters);
    }

    private handleLoadSummaryResponse (inventory: Inventory) {
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

    private handleBreakdownResponse (key: string, breakdown: FilterOption[]) {
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
}
