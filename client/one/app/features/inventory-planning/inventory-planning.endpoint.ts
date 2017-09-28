import {Injectable} from '@angular/core';
import {HttpClient, HttpParams} from '@angular/common/http';
import {Observable} from 'rxjs/Observable';
import 'rxjs/add/observable/of';
import 'rxjs/add/operator/delay';
import 'rxjs/add/operator/map';
import 'rxjs/add/operator/catch';

import {Inventory} from './types/inventory';
import {AvailableFilterOption} from './types/available-filter-option';
import {SelectedFilters} from './types/selected-filters';
import {SelectedFilterOption} from './types/selected-filter-option';

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

interface InventoryResponse {
    data: any;
}

const enum FilterField {
    Country,
    Device,
    Publisher,
}


@Injectable()
export class InventoryPlanningEndpoint {
    constructor (private http: HttpClient) {}

    loadSummary (selectedFilters: SelectedFilters): Observable<Inventory> {
        const {method, params, body} = this.buildRequestProperties(selectedFilters);
        return this.http.request<InventoryResponse>(
            method,
            '/rest/internal/inventory-planning/summary',
            {params: params, body: body})
            .map(res => res.data);
    }

    loadCountries (selectedFilters: SelectedFilters): Observable<AvailableFilterOption[]> {
        const {method, params, body} = this.buildRequestProperties(selectedFilters, FilterField.Country);
        return this.http.request<InventoryResponse>(
            method,
            '/rest/internal/inventory-planning/countries',
            {params: params, body: body})
            .map(res => res.data);
    }

    loadPublishers (selectedFilters: SelectedFilters): Observable<AvailableFilterOption[]> {
        const {method, params, body} = this.buildRequestProperties(selectedFilters, FilterField.Publisher);
        return this.http.request<InventoryResponse>(
            method,
            '/rest/internal/inventory-planning/publishers',
            {params: params, body: body})
            .map(res => res.data);
    }

    loadDevices (selectedFilters: SelectedFilters): Observable<AvailableFilterOption[]> {
        const {method, params, body} = this.buildRequestProperties(selectedFilters, FilterField.Device);
        return this.http.request<InventoryResponse>(
            method,
            '/rest/internal/inventory-planning/device-types',
            {params: params, body: body})
            .map(res => res.data);
    }

    private buildRequestProperties (selectedFilters: SelectedFilters,
                                    excludeFilterField?: FilterField): RequestProperties {
        const filterPayload = this.buildFilterPayload(selectedFilters, excludeFilterField);
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

    private buildFilterPayload (selectedFilters: SelectedFilters,
                                excludeFilterField?: FilterField): FilterPayload {
        const payload: FilterPayload = {c: [], p: [], d: []};
        if (excludeFilterField !== FilterField.Country) {
            payload.c = selectedFilters.countries.map((x: SelectedFilterOption) => x.value);
        }
        if (excludeFilterField !== FilterField.Publisher) {
            payload.p = selectedFilters.publishers.map((x: SelectedFilterOption) => x.value);
        }
        if (excludeFilterField !== FilterField.Device) {
            payload.d = selectedFilters.devices.map((x: SelectedFilterOption) => x.value);
        }
        return payload;
    }
}
