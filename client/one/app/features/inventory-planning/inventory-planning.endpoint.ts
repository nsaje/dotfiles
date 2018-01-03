import {Injectable} from '@angular/core';
import {HttpClient, HttpParams} from '@angular/common/http';
import {Observable} from 'rxjs/Observable';
import {map} from 'rxjs/operators';

import {RestApiResponse} from '../../shared/types/rest-api-response';
import {Inventory} from './types/inventory';
import {Filters} from './types/filters';
import {FilterOption} from './types/filter-option';

const MAX_QUERY_PARAMS_LENGTH = 1900;

interface FilterPayload {
    c: string[];
    p: string[];
    d: string[];
}

interface RequestProperties {
    method: string;
    params: HttpParams;
    body: FilterPayload;
}

@Injectable()
export class InventoryPlanningEndpoint {
    constructor (private http: HttpClient) {}

    loadSummary (selectedFilters: Filters): Observable<Inventory> {
        const {method, params, body} = this.buildRequestProperties(selectedFilters);
        return this.http.request<RestApiResponse>(
                method,
                '/rest/internal/inventory-planning/summary',
                {params: params, body: body}
            )
            .pipe(
                map(res => res.data)
            );
    }

    loadCountries (selectedFilters: Filters): Observable<FilterOption[]> {
        const {method, params, body} = this.buildRequestProperties(selectedFilters);
        return this.http.request<RestApiResponse>(
                method,
                '/rest/internal/inventory-planning/countries',
                {params: params, body: body}
            )
            .pipe(
                map(res => res.data),
                map(this.convertOptionsValueToSting)
            );
    }

    loadPublishers (selectedFilters: Filters): Observable<FilterOption[]> {
        const {method, params, body} = this.buildRequestProperties(selectedFilters);
        return this.http.request<RestApiResponse>(
                method,
                '/rest/internal/inventory-planning/publishers',
                {params: params, body: body}
            )
            .pipe(
                map(res => res.data),
                map(this.convertOptionsValueToSting)
            );
    }

    loadDevices (selectedFilters: Filters): Observable<FilterOption[]> {
        const {method, params, body} = this.buildRequestProperties(selectedFilters);
        return this.http.request<RestApiResponse>(
                method,
                '/rest/internal/inventory-planning/device-types',
                {params: params, body: body}
            )
            .pipe(
                map(res => res.data),
                map(this.convertOptionsValueToSting)
            );
    }

    private buildRequestProperties (selectedFilters: Filters): RequestProperties {
        const filterPayload = this.buildFilterPayload(selectedFilters);
        let params = new HttpParams();
        for (const filter of Object.keys(filterPayload)) {
            if (filterPayload[filter].length) {
                params = params.set(filter, filterPayload[filter]);
            }
        }
        if (params.toString().length < MAX_QUERY_PARAMS_LENGTH) {
            return {method: 'GET', params: params, body: null};
        } else {
            return {method: 'POST', params: null, body: filterPayload};
        }
    }

    private buildFilterPayload (selectedFilters: Filters): FilterPayload {
        return {
            c: selectedFilters.countries.map((x: FilterOption) => x.value),
            p: selectedFilters.publishers.map((x: FilterOption) => x.value),
            d: selectedFilters.devices.map((x: FilterOption) => x.value),
        };
    }

    private convertOptionsValueToSting (options: FilterOption[]): FilterOption[] {
        return options.map(option => {
            return {
                ...option,
                value: option.value ? option.value.toString() : '',
            };
        });
    }
}
