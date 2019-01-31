import {Filters} from '../types/filters';
import {RequestPayload} from '../../../shared/types/request-payload';

export function buildRequestPayload(selectedFilters: Filters): RequestPayload {
    return {
        countries: selectedFilters.countries.map((x: any) => x.value),
        publishers: selectedFilters.publishers.map((x: any) => x.value),
        devices: selectedFilters.devices.map((x: any) => x.value),
        sources: selectedFilters.sources.map((x: any) => x.value),
    };
}
