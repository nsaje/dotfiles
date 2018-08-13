import {Injectable} from '@angular/core';
import {HttpClient, HttpParams, HttpErrorResponse} from '@angular/common/http';
import {Observable, throwError} from 'rxjs';
import {map, catchError} from 'rxjs/operators';

import {Filters} from '../types/filters';
import {Inventory} from '../types/inventory';
import {ApiResponse} from '../../../shared/types/api-response';
import {FilterOption} from '../types/filter-option';
import {StoreEndpoint} from '../../../shared/types/store-endpoint';
import {InventoryPlanningStore} from './inventory-planning.store';
import {RequestProperties} from '../types/request-properties';
import {FilterPayload} from '../types/filter-payload';

const MAX_QUERY_PARAMS_LENGTH = 1900;

@Injectable()
export class InventoryPlanningEndpoint extends StoreEndpoint {
    constructor(private http: HttpClient) {
        super();
    }

    loadSummary(
        store: InventoryPlanningStore,
        selectedFilters: Filters
    ): Observable<Inventory> {
        const REQUEST_NAME = 'summary';

        const {method, params, body} = this.buildRequestProperties(
            selectedFilters
        );

        this.setRequestState(store, REQUEST_NAME, {
            inProgress: true,
        });

        return this.http
            .request<ApiResponse>(
                method,
                '/rest/internal/inventory-planning/summary',
                {params: params, body: body}
            )
            .pipe(
                map((response: ApiResponse) => {
                    this.setRequestState(store, REQUEST_NAME, {
                        inProgress: false,
                    });

                    return response.data;
                }),
                catchError((error: HttpErrorResponse) => {
                    this.setRequestState(store, REQUEST_NAME, {
                        inProgress: false,
                        error: true,
                        errorMessage: error.message,
                    });

                    return throwError(error);
                })
            );
    }

    loadCountries(
        store: InventoryPlanningStore,
        selectedFilters: Filters
    ): Observable<FilterOption[]> {
        const REQUEST_NAME = 'countries';

        const {method, params, body} = this.buildRequestProperties(
            selectedFilters
        );

        this.setRequestState(store, REQUEST_NAME, {
            inProgress: true,
        });

        return this.http
            .request<ApiResponse>(
                method,
                '/rest/internal/inventory-planning/countries',
                {params: params, body: body}
            )
            .pipe(
                map((response: ApiResponse) => {
                    this.setRequestState(store, REQUEST_NAME, {
                        inProgress: false,
                    });

                    return response.data;
                }),
                map(this.convertOptionsValueToString),
                catchError((error: HttpErrorResponse) => {
                    this.setRequestState(store, REQUEST_NAME, {
                        inProgress: false,
                        error: true,
                        errorMessage: error.message,
                    });

                    return throwError(error);
                })
            );
    }

    loadPublishers(
        store: InventoryPlanningStore,
        selectedFilters: Filters
    ): Observable<FilterOption[]> {
        const REQUEST_NAME = 'publishers';

        const {method, params, body} = this.buildRequestProperties(
            selectedFilters
        );

        this.setRequestState(store, REQUEST_NAME, {
            inProgress: true,
        });

        return this.http
            .request<ApiResponse>(
                method,
                '/rest/internal/inventory-planning/publishers',
                {params: params, body: body}
            )
            .pipe(
                map((response: ApiResponse) => {
                    this.setRequestState(store, REQUEST_NAME, {
                        inProgress: false,
                    });

                    return response.data;
                }),
                map(this.convertOptionsValueToString),
                catchError((error: HttpErrorResponse) => {
                    this.setRequestState(store, REQUEST_NAME, {
                        inProgress: false,
                        error: true,
                        errorMessage: error.message,
                    });

                    return throwError(error);
                })
            );
    }

    loadDevices(
        store: InventoryPlanningStore,
        selectedFilters: Filters
    ): Observable<FilterOption[]> {
        const REQUEST_NAME = 'devices';

        const {method, params, body} = this.buildRequestProperties(
            selectedFilters
        );

        this.setRequestState(store, REQUEST_NAME, {
            inProgress: true,
        });

        return this.http
            .request<ApiResponse>(
                method,
                '/rest/internal/inventory-planning/device-types',
                {params: params, body: body}
            )
            .pipe(
                map((response: ApiResponse) => {
                    this.setRequestState(store, REQUEST_NAME, {
                        inProgress: false,
                    });

                    return response.data;
                }),
                map(this.convertOptionsValueToString),
                catchError((error: HttpErrorResponse) => {
                    this.setRequestState(store, REQUEST_NAME, {
                        inProgress: false,
                        error: true,
                        errorMessage: error.message,
                    });

                    return throwError(error);
                })
            );
    }

    loadSources(
        store: InventoryPlanningStore,
        selectedFilters: Filters
    ): Observable<FilterOption[]> {
        const REQUEST_NAME = 'sources';

        const {method, params, body} = this.buildRequestProperties(
            selectedFilters
        );

        this.setRequestState(store, REQUEST_NAME, {
            inProgress: true,
        });

        return this.http
            .request<ApiResponse>(
                method,
                '/rest/internal/inventory-planning/media-sources',
                {params: params, body: body}
            )
            .pipe(
                map((response: ApiResponse) => {
                    this.setRequestState(store, REQUEST_NAME, {
                        inProgress: false,
                    });

                    return response.data;
                }),
                map(this.convertOptionsValueToString),
                catchError((error: HttpErrorResponse) => {
                    this.setRequestState(store, REQUEST_NAME, {
                        inProgress: false,
                        error: true,
                        errorMessage: error.message,
                    });

                    return throwError(error);
                })
            );
    }

    private buildRequestProperties(
        selectedFilters: Filters
    ): RequestProperties {
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

    private buildFilterPayload(selectedFilters: Filters): FilterPayload {
        return {
            countries: selectedFilters.countries.map(
                (x: FilterOption) => x.value
            ),
            publishers: selectedFilters.publishers.map(
                (x: FilterOption) => x.value
            ),
            devices: selectedFilters.devices.map((x: FilterOption) => x.value),
            sources: selectedFilters.sources.map((x: FilterOption) => x.value),
        };
    }

    private convertOptionsValueToString(
        options: FilterOption[]
    ): FilterOption[] {
        return options.map(option => {
            return {
                ...option,
                value: option.value ? option.value.toString() : '',
            };
        });
    }
}
