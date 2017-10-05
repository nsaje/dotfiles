import {Injectable} from '@angular/core';

import {Store} from '../../shared/types/store';
import {InventoryPlanningState} from './inventory-planning-state';
import {InventoryPlanningEndpoint} from './inventory-planning.endpoint';
import {AvailableFilterOption} from './types/available-filter-option';
import {SelectedFilters} from './types/selected-filters';
import {SelectedFilterOption} from './types/selected-filter-option';

@Injectable()
export class InventoryPlanningStore extends Store<InventoryPlanningState> {
    constructor (private endpoint: InventoryPlanningEndpoint) {
        super(new InventoryPlanningState());

        this.refreshData(this.state.selectedFilters);
    }

    private refreshData (selectedFilters: SelectedFilters) {
        this.setState({
            ...this.state,
            requests: {
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
            },
        });

        this.endpoint.loadSummary(selectedFilters).subscribe(inventory => {
            this.setState({
                ...this.state,
                inventory: inventory,
                requests: {
                    ...this.state.requests,
                    summary: {
                        ...this.state.requests.summary,
                        inProgress: false,
                    },
                },
            });
        });
        this.endpoint.loadCountries(selectedFilters).subscribe(countries => {
            this.setState({
                ...this.state,
                availableFilters: {
                    ...this.state.availableFilters,
                    countries: countries,
                },
                requests: {
                    ...this.state.requests,
                    countries: {
                        ...this.state.requests.countries,
                        inProgress: false,
                    },
                },
            });
        });
        this.endpoint.loadPublishers(selectedFilters).subscribe(publishers => {
            this.setState({
                ...this.state,
                availableFilters: {
                    ...this.state.availableFilters,
                    publishers: publishers,
                },
                requests: {
                    ...this.state.requests,
                    publishers: {
                        ...this.state.requests.publishers,
                        inProgress: false,
                    },
                },
            });
        });
        this.endpoint.loadDevices(selectedFilters).subscribe(devices => {
            this.setState({
                ...this.state,
                availableFilters: {
                    ...this.state.availableFilters,
                    devices: devices,
                },
                requests: {
                    ...this.state.requests,
                    devices: {
                        ...this.state.requests.devices,
                        inProgress: false,
                    },
                },
            });
        });
    }

    toggleCountry (value: string): void {
        this.toggleOption('countries', value);
    }

    togglePublisher (value: string): void {
        this.toggleOption('publishers', value);
    }

    toggleDevice (value: string): void {
        this.toggleOption('devices', value);
    }

    removeOption ($event: {key: string, value: string}): void {
        this.toggleOption($event.key, $event.value);
    }

    private toggleOption (key: string, value: string) {
        this.setState({
            ...this.state,
            selectedFilters: {
                ...this.state.selectedFilters,
                [key]: this.getSelectedWithToggledOption(
                    this.state.availableFilters[key],
                    this.state.selectedFilters[key],
                    value
                ),
            },
        });
        this.refreshData(this.state.selectedFilters);
    }

    private getSelectedWithToggledOption (
        available: AvailableFilterOption[],
        selected: SelectedFilterOption[],
        value: string
    ): SelectedFilterOption[] {
        const selectedWithNoToggledOption = selected.filter(i => i.value !== value);
        if (selectedWithNoToggledOption.length === selected.length) {
            for (const filter of available) {
                if (filter.value === value) {
                    return [...selectedWithNoToggledOption, {value: filter.value, name: filter.name}];
                }
            }
        }
        return selectedWithNoToggledOption;
    }
}
