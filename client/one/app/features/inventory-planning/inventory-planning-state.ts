import {Requests} from './types/requests';
import {Filters} from './types/filters';
import {Inventory} from './types/inventory';

export class InventoryPlanningState {
    requests: Requests = {
        summary: {},
        countries: {},
        publishers: {},
        devices: {},
        sources: {},
    };
    selectedFilters: Filters = {
        countries: [],
        publishers: [],
        devices: [],
        sources: [],
    };
    availableFilters: Filters = {
        countries: [],
        publishers: [],
        devices: [],
        sources: [],
    };
    inventory: Inventory = {
        auctionCount: null,
        avgCpm: null,
        winRatio: null,
    };
}
