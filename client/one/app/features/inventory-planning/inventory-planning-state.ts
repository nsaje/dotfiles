import {Requests} from './types/requests';
import {Filters} from './types/filters';
import {Inventory} from './types/inventory';

export class InventoryPlanningState {
    requests: Requests = {
        summary: {},
        countries: {},
        publishers: {},
        devices: {},
    };
    selectedFilters: Filters = {
        countries: [],
        publishers: [],
        devices: [],
    };
    availableFilters: Filters = {
        countries: [],
        publishers: [],
        devices: [],
    };
    inventory: Inventory = {
        auctionCount: null,
        avgCpm: null,
        winRatio: null,
    };
}
