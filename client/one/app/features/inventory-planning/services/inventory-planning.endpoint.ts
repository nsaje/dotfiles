import {Injectable} from '@angular/core';
import {HttpClient, HttpErrorResponse} from '@angular/common/http';
import {Observable, throwError} from 'rxjs';
import {map, catchError} from 'rxjs/operators';

import {Filters} from '../types/filters';
import {Inventory} from '../types/inventory';
import {FilterOption} from '../types/filter-option';
import {ApiResponse} from '../../../shared/types/api-response';
import {StoreEndpoint} from '../../../shared/types/store-endpoint';
import {RequestPayload} from '../../../shared/types/request-payload';
import {InventoryPlanningStore} from './inventory-planning.store';
import {INVENTORY_PLANNING_CONFIG} from '../inventory-planning.config';
import * as endpointHelpers from '../../../shared/helpers/endpoint.helpers';

@Injectable()
export class InventoryPlanningEndpoint extends StoreEndpoint {
    constructor(private http: HttpClient) {
        super();
    }

    loadSummary(
        store: InventoryPlanningStore,
        selectedFilters: Filters
    ): Observable<Inventory> {
        const request = INVENTORY_PLANNING_CONFIG.requests.loadSummary;

        const requestPayload = this.buildRequestPayload(selectedFilters);
        const requestProperties = endpointHelpers.buildRequestProperties(
            requestPayload
        );

        this.setRequestState(store, request, {
            inProgress: true,
        });

        return this.http
            .request<ApiResponse<any>>(requestProperties.method, request.url, {
                params: requestProperties.params,
                body: requestProperties.body,
            })
            .pipe(
                map((response: ApiResponse<any>) => {
                    this.setRequestState(store, request, {
                        inProgress: false,
                    });

                    return response.data;
                }),
                catchError((error: HttpErrorResponse) => {
                    this.setRequestState(store, request, {
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
        const request = INVENTORY_PLANNING_CONFIG.requests.loadCountries;

        const requestPayload = this.buildRequestPayload(selectedFilters);
        const requestProperties = endpointHelpers.buildRequestProperties(
            requestPayload
        );

        this.setRequestState(store, request, {
            inProgress: true,
        });

        return this.http
            .request<ApiResponse<any>>(requestProperties.method, request.url, {
                params: requestProperties.params,
                body: requestProperties.body,
            })
            .pipe(
                map((response: ApiResponse<any>) => {
                    this.setRequestState(store, request, {
                        inProgress: false,
                    });

                    return response.data;
                }),
                map(this.convertOptionsValueToString),
                catchError((error: HttpErrorResponse) => {
                    this.setRequestState(store, request, {
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
        const request = INVENTORY_PLANNING_CONFIG.requests.loadPublishers;

        const requestPayload = this.buildRequestPayload(selectedFilters);
        const requestProperties = endpointHelpers.buildRequestProperties(
            requestPayload
        );

        this.setRequestState(store, request, {
            inProgress: true,
        });

        return this.http
            .request<ApiResponse<any>>(requestProperties.method, request.url, {
                params: requestProperties.params,
                body: requestProperties.body,
            })
            .pipe(
                map((response: ApiResponse<any>) => {
                    this.setRequestState(store, request, {
                        inProgress: false,
                    });

                    return response.data;
                }),
                map(this.convertOptionsValueToString),
                catchError((error: HttpErrorResponse) => {
                    this.setRequestState(store, request, {
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
        const request = INVENTORY_PLANNING_CONFIG.requests.loadDevices;

        const requestPayload = this.buildRequestPayload(selectedFilters);
        const requestProperties = endpointHelpers.buildRequestProperties(
            requestPayload
        );

        this.setRequestState(store, request, {
            inProgress: true,
        });

        return this.http
            .request<ApiResponse<any>>(requestProperties.method, request.url, {
                params: requestProperties.params,
                body: requestProperties.body,
            })
            .pipe(
                map((response: ApiResponse<any>) => {
                    this.setRequestState(store, request, {
                        inProgress: false,
                    });

                    return response.data;
                }),
                map(this.convertOptionsValueToString),
                catchError((error: HttpErrorResponse) => {
                    this.setRequestState(store, request, {
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
        const request = INVENTORY_PLANNING_CONFIG.requests.loadSources;

        const requestPayload = this.buildRequestPayload(selectedFilters);
        const requestProperties = endpointHelpers.buildRequestProperties(
            requestPayload
        );

        this.setRequestState(store, request, {
            inProgress: true,
        });

        return this.http
            .request<ApiResponse<any>>(requestProperties.method, request.url, {
                params: requestProperties.params,
                body: requestProperties.body,
            })
            .pipe(
                map((response: ApiResponse<any>) => {
                    this.setRequestState(store, request, {
                        inProgress: false,
                    });

                    return response.data;
                }),
                map(this.convertOptionsValueToString),
                catchError((error: HttpErrorResponse) => {
                    this.setRequestState(store, request, {
                        inProgress: false,
                        error: true,
                        errorMessage: error.message,
                    });

                    return throwError(error);
                })
            );
    }

    /**
     * The following function is used to convert
     * Filters to RequestPayload.
     * @param selectedFilters
     */
    private buildRequestPayload(selectedFilters: Filters): RequestPayload {
        return {
            countries: selectedFilters.countries.map((x: any) => x.value),
            publishers: selectedFilters.publishers.map((x: any) => x.value),
            devices: selectedFilters.devices.map((x: any) => x.value),
            sources: selectedFilters.sources.map((x: any) => x.value),
        };
    }

    /**
     * The following function is used to convert
     * options value to string type.
     * @param options
     */
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
