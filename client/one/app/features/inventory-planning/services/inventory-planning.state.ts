import {Filters} from '../types/filters';
import {Inventory} from '../types/inventory';
import {RequestState} from '../../../shared/types/request-state';

export class InventoryPlanningState {
    requests = {
        summary: {} as RequestState,
        countries: {} as RequestState,
        publishers: {} as RequestState,
        devices: {} as RequestState,
        sources: {} as RequestState,
        channels: {} as RequestState,
    };
    selectedFilters: Filters = {
        countries: [],
        publishers: [],
        devices: [],
        sources: [],
        channels: [],
    };
    availableFilters: Filters = {
        countries: [],
        publishers: [],
        devices: [],
        sources: [],
        channels: [],
    };
    inventory: Inventory = {
        auctionCount: null,
        avgCpm: null,
        avgCpc: null,
        winRatio: null,
    };
}
