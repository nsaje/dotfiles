import {Injectable} from '@angular/core';
import {HttpClient, HttpErrorResponse} from '@angular/common/http';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {Observable, throwError} from 'rxjs';
import {ApiResponse} from '../../../shared/types/api-response';
import {map, catchError} from 'rxjs/operators';
import {PublisherGroup} from '../types/publisher-group';
import * as commonHelpers from '../../../shared/helpers/common.helpers';
import {PUBLISHER_GROUPS_CONFIG} from './publisher-groups.config';
import {
    convertToFormData,
    replaceUrl,
} from '../../../shared/helpers/endpoint.helpers';
import {
    getValueWithOnlyProps,
    isPrimitive,
} from '../../../shared/helpers/common.helpers';
import * as deepmerge from 'deepmerge';

@Injectable()
export class PublisherGroupsEndpoint {
    constructor(private http: HttpClient) {}

    search(
        agencyId: string | null,
        accountId: string | null,
        keyword: string | null,
        offset: number | null,
        limit: number | null,
        includeImplicit: boolean,
        requestStateUpdater: RequestStateUpdater
    ): Observable<PublisherGroup[]> {
        const request = PUBLISHER_GROUPS_CONFIG.requests.publisherGroups.search;

        const params = {
            offset: `${offset}`,
            limit: `${limit}`,
            includeImplicit: `${includeImplicit}`,
            ...(commonHelpers.isDefined(agencyId) && {agencyId}),
            ...(commonHelpers.isDefined(accountId) && {accountId}),
            ...(commonHelpers.isDefined(keyword) && {keyword}),
        };

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .get<ApiResponse<PublisherGroup[]>>(request.url, {
                params: params,
            })
            .pipe(
                map(response => {
                    requestStateUpdater(request.name, {
                        inProgress: false,
                        count: response.count,
                        next: response.next,
                        previous: response.previous,
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

    list(
        agencyId: string | null,
        accountId: string | null,
        requestStateUpdater: RequestStateUpdater
    ): Observable<PublisherGroup[]> {
        const request = PUBLISHER_GROUPS_CONFIG.requests.publisherGroups.list;

        const params: any = {
            ...(commonHelpers.isDefined(agencyId) && {agency_id: agencyId}),
            ...(commonHelpers.isDefined(accountId) && {account_id: accountId}),
        };

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .get<ApiResponse<any>>(request.url, {params})
            .pipe(
                map(response => {
                    requestStateUpdater(request.name, {
                        inProgress: false,
                        count: response.count,
                        next: response.next,
                        previous: response.previous,
                    });
                    return this.snakeObjectToCamelCase<PublisherGroup[]>(
                        response.data.publisher_groups
                    );
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

    upload(
        publisherGroup: PublisherGroup,
        requestStateUpdater: RequestStateUpdater
    ): Observable<PublisherGroup> {
        const request =
            PUBLISHER_GROUPS_CONFIG.requests?.publisherGroups.upload;

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        // The current backend only accepts a limited number of properties, later this can be removed
        const publisherGroupUpload: Partial<PublisherGroup> = getValueWithOnlyProps(
            publisherGroup,
            [
                'id',
                'name',
                'entries',
                'includeSubdomains',
                'accountId',
                'agencyId',
            ]
        );
        const snakeCased: any = this.camelObjectToSnakeCase(
            publisherGroupUpload
        );
        const formData: FormData = convertToFormData(snakeCased);
        return this.http
            .post<ApiResponse<PublisherGroup>>(request.url, formData)
            .pipe(
                map(response => {
                    requestStateUpdater(request.name, {
                        inProgress: false,
                    });
                    return response.data;
                }),
                catchError((error: HttpErrorResponse) => {
                    error = this.snakeObjectToCamelCase(error);
                    this.convertLegacyFieldErrors(error);
                    requestStateUpdater(request.name, {
                        inProgress: false,
                        error: true,
                        errorMessage: error.message,
                    });
                    return throwError(error);
                })
            );
    }

    remove(
        publisherGroupId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<void> {
        const request = replaceUrl(
            PUBLISHER_GROUPS_CONFIG.requests.publisherGroups.remove,
            {publisherGroupId: publisherGroupId}
        );

        return this.http.delete(`${request.url}`).pipe(
            map(() => {
                requestStateUpdater(request.name, {
                    inProgress: false,
                });
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

    download(publisherGroupId: string) {
        const request = replaceUrl(
            PUBLISHER_GROUPS_CONFIG.requests.publisherGroups.download,
            {
                publisherGroupId: publisherGroupId,
            }
        );
        window.open(request.url, '_blank');
    }

    downloadErrors(publisherGroup: PublisherGroup, csvKey: string) {
        const request = replaceUrl(
            PUBLISHER_GROUPS_CONFIG.requests.publisherGroups.downloadErrors,
            {
                csvKey: csvKey,
            }
        );
        if (commonHelpers.isDefined(publisherGroup.accountId)) {
            request.url = `${request.url}?account_id=${publisherGroup.accountId}`;
        } else if (commonHelpers.isDefined(publisherGroup.agencyId)) {
            request.url = `${request.url}?agency_id=${publisherGroup.agencyId}`;
        }
        window.open(request.url, '_blank');
    }

    downloadExample() {
        const request =
            PUBLISHER_GROUPS_CONFIG.requests.publisherGroups.downloadExample;
        window.open(request.url, '_blank');
    }

    /** This is temporary until the backend gets updated */
    convertLegacyFieldErrors(errors: HttpErrorResponse): void {
        if (
            commonHelpers.isDefined(errors.error) &&
            commonHelpers.isDefined(errors.error.data) &&
            commonHelpers.isDefined(errors.error.data.errors)
        ) {
            errors.error.details = deepmerge(
                errors.error.details || {},
                errors.error.data.errors
            );
        }
    }

    /** This is temporary until the backend gets updated */
    snakePropertyToCamelCase(snakeKey: string): string {
        return snakeKey
            .split('_')
            .map((x, i) => (i === 0 ? x : x[0].toUpperCase() + x.slice(1)))
            .join('');
    }

    /** This is temporary until the backend gets updated */
    camelPropertyToSnakeCase(camelKey: string): string {
        return Array.from(camelKey)
            .map(x => (x === x.toUpperCase() ? '_' + x.toLowerCase() : x))
            .join('');
    }

    /** This is temporary until the backend gets updated */
    snakeObjectToCamelCase<T>(snakeCased: any): T {
        return this.convertObjectCase(
            snakeCased,
            this.snakePropertyToCamelCase.bind(this)
        );
    }

    /** This is temporary until the backend gets updated */
    camelObjectToSnakeCase<T>(camelCased: any): T {
        return this.convertObjectCase(
            camelCased,
            this.camelPropertyToSnakeCase.bind(this)
        );
    }

    /** This is temporary until the backend gets updated */
    private convertObjectCase<T>(
        originalObject: any,
        convertProperty: (x: string) => string
    ): T {
        let convertedObject: any = {};

        if (isPrimitive(originalObject)) {
            convertedObject = originalObject;
        } else if (Array.isArray(originalObject)) {
            convertedObject = <any[]>(
                originalObject.map(x =>
                    this.convertObjectCase(x, convertProperty)
                )
            );
        } else if (Object.keys(originalObject).length > 0) {
            Object.keys(originalObject).forEach(originalKey => {
                const originalValue: any = originalObject[originalKey];
                const convertedKey: string = convertProperty(originalKey);
                const convertedValue: any = this.convertObjectCase(
                    originalValue,
                    convertProperty
                );

                convertedObject[convertedKey] = convertedValue;
            });
        } else {
            convertedObject = originalObject;
        }

        return <T>convertedObject;
    }
}
