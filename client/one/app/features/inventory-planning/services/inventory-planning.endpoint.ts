import {Injectable} from '@angular/core';
import {HttpClient, HttpErrorResponse} from '@angular/common/http';
import {Observable, throwError} from 'rxjs';
import {map, catchError} from 'rxjs/operators';

import {Filters} from '../types/filters';
import {Inventory} from '../types/inventory';
import {FilterOption} from '../types/filter-option';
import {ApiResponse} from '../../../shared/types/api-response';
import {INVENTORY_PLANNING_CONFIG} from '../inventory-planning.config';
import * as endpointHelpers from '../../../shared/helpers/endpoint.helpers';
import * as requestPayloadHelpers from '../helpers/request-payload.helpers';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';

@Injectable()
export class InventoryPlanningEndpoint {
    constructor(private http: HttpClient) {}

    loadSummary(
        selectedFilters: Filters,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Inventory> {
        const request = INVENTORY_PLANNING_CONFIG.requests.loadSummary;

        const requestPayload = requestPayloadHelpers.buildRequestPayload(
            selectedFilters
        );
        const requestProperties = endpointHelpers.buildRequestProperties(
            requestPayload
        );

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .request<ApiResponse<any>>(requestProperties.method, request.url, {
                params: requestProperties.params,
                body: requestProperties.body,
            })
            .pipe(
                map((response: ApiResponse<any>) => {
                    requestStateUpdater(request.name, {
                        inProgress: false,
                    });

                    return response.data;
                }),
                catchError((error: HttpErrorResponse) => {
                    requestStateUpdater(request.name, {
                        inProgress: false,
                        error: true,
                        errorMessage: error.message,
                    });

                    return throwError(error);
                })
            );
    }

    loadCountries(
        selectedFilters: Filters,
        requestStateUpdater: RequestStateUpdater
    ): Observable<FilterOption[]> {
        const request = INVENTORY_PLANNING_CONFIG.requests.loadCountries;

        const requestPayload = requestPayloadHelpers.buildRequestPayload(
            selectedFilters
        );
        const requestProperties = endpointHelpers.buildRequestProperties(
            requestPayload
        );

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .request<ApiResponse<any>>(requestProperties.method, request.url, {
                params: requestProperties.params,
                body: requestProperties.body,
            })
            .pipe(
                map((response: ApiResponse<any>) => {
                    requestStateUpdater(request.name, {
                        inProgress: false,
                    });

                    return response.data;
                }),
                map(this.convertOptionsValueToString),
                catchError((error: HttpErrorResponse) => {
                    requestStateUpdater(request.name, {
                        inProgress: false,
                        error: true,
                        errorMessage: error.message,
                    });

                    return throwError(error);
                })
            );
    }

    loadPublishers(
        selectedFilters: Filters,
        requestStateUpdater: RequestStateUpdater
    ): Observable<FilterOption[]> {
        const request = INVENTORY_PLANNING_CONFIG.requests.loadPublishers;

        const requestPayload = requestPayloadHelpers.buildRequestPayload(
            selectedFilters
        );
        const requestProperties = endpointHelpers.buildRequestProperties(
            requestPayload
        );

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .request<ApiResponse<any>>(requestProperties.method, request.url, {
                params: requestProperties.params,
                body: requestProperties.body,
            })
            .pipe(
                map((response: ApiResponse<any>) => {
                    requestStateUpdater(request.name, {
                        inProgress: false,
                    });

                    return response.data;
                }),
                map(this.convertOptionsValueToString),
                catchError((error: HttpErrorResponse) => {
                    requestStateUpdater(request.name, {
                        inProgress: false,
                        error: true,
                        errorMessage: error.message,
                    });

                    return throwError(error);
                })
            );
    }

    loadDevices(
        selectedFilters: Filters,
        requestStateUpdater: RequestStateUpdater
    ): Observable<FilterOption[]> {
        const request = INVENTORY_PLANNING_CONFIG.requests.loadDevices;

        const requestPayload = requestPayloadHelpers.buildRequestPayload(
            selectedFilters
        );
        const requestProperties = endpointHelpers.buildRequestProperties(
            requestPayload
        );

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .request<ApiResponse<any>>(requestProperties.method, request.url, {
                params: requestProperties.params,
                body: requestProperties.body,
            })
            .pipe(
                map((response: ApiResponse<any>) => {
                    requestStateUpdater(request.name, {
                        inProgress: false,
                    });

                    return response.data;
                }),
                map(this.convertOptionsValueToString),
                catchError((error: HttpErrorResponse) => {
                    requestStateUpdater(request.name, {
                        inProgress: false,
                        error: true,
                        errorMessage: error.message,
                    });

                    return throwError(error);
                })
            );
    }

    loadSources(
        selectedFilters: Filters,
        requestStateUpdater: RequestStateUpdater
    ): Observable<FilterOption[]> {
        const request = INVENTORY_PLANNING_CONFIG.requests.loadSources;

        const requestPayload = requestPayloadHelpers.buildRequestPayload(
            selectedFilters
        );
        const requestProperties = endpointHelpers.buildRequestProperties(
            requestPayload
        );

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .request<ApiResponse<any>>(requestProperties.method, request.url, {
                params: requestProperties.params,
                body: requestProperties.body,
            })
            .pipe(
                map((response: ApiResponse<any>) => {
                    requestStateUpdater(request.name, {
                        inProgress: false,
                    });

                    return response.data;
                }),
                map(this.convertOptionsValueToString),
                catchError((error: HttpErrorResponse) => {
                    requestStateUpdater(request.name, {
                        inProgress: false,
                        error: true,
                        errorMessage: error.message,
                    });

                    return throwError(error);
                })
            );
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
