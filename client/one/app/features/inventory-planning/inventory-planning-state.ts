import {SelectedFilters} from './types/selected-filters';
import {AvailableFilters} from './types/available-filters';
import {Inventory} from './types/inventory';

export class InventoryPlanningState {
    selectedFilters: SelectedFilters = {
        countries: [],
        publishers: [],
        devices: [],
    };
    availableFilters: AvailableFilters = {
        countries: [],
        publishers: [],
        devices: [],
    };
    inventory: Inventory = {
        auctionCount: null,
        avgCpm: null,
    };
}
