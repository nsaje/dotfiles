import {Injectable} from '@angular/core';
import {HttpClient, HttpErrorResponse} from '@angular/common/http';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {Observable, throwError} from 'rxjs';
import {ApiResponse} from '../../../shared/types/api-response';
import {map, catchError} from 'rxjs/operators';
import {PublisherGroup} from '../types/publisher-group';
import * as commonHelpers from '../../../shared/helpers/common.helpers';
import {PUBLISHER_GROUPS_CONFIG} from '../publisher-groups.config';
import {
    convertToFormData,
    replaceUrl,
} from '../../../shared/helpers/endpoint.helpers';
import {
    getValueWithOnlyProps,
    isPrimitive,
} from '../../../shared/helpers/common.helpers';
import * as deepmerge from 'deepmerge';
import {HttpRequestInfo} from '../../../shared/types/http-request-info';
import {PublisherGroupWithEntries} from '../types/publisher-group-with-entries';
import {PublisherGroupConnection} from '../types/publisher-group-connection';

@Injectable()
export class PublisherGroupsEndpoint {
    constructor(private http: HttpClient) {}

    listImplicit(
        agencyId: string | null,
        accountId: string | null,
        keyword: string | null,
        offset: number | null,
        limit: number | null,
        requestStateUpdater: RequestStateUpdater
    ): Observable<PublisherGroup[]> {
        return this.list(
            agencyId,
            accountId,
            keyword,
            offset,
            limit,
            true,
            PUBLISHER_GROUPS_CONFIG.requests.publisherGroups.listImplicit,
            requestStateUpdater
        );
    }

    listExplicit(
        agencyId: string | null,
        accountId: string | null,
        keyword: string | null,
        offset: number | null,
        limit: number | null,
        requestStateUpdater: RequestStateUpdater
    ): Observable<PublisherGroup[]> {
        return this.list(
            agencyId,
            accountId,
            keyword,
            offset,
            limit,
            false,
            PUBLISHER_GROUPS_CONFIG.requests.publisherGroups.listExplicit,
            requestStateUpdater
        );
    }

    private list(
        agencyId: string | null,
        accountId: string | null,
        keyword: string | null,
        offset: number | null,
        limit: number | null,
        implicit: boolean,
        request: HttpRequestInfo,
        requestStateUpdater: RequestStateUpdater
    ): Observable<PublisherGroup[]> {
        const params = {
            offset: `${offset}`,
            limit: `${limit}`,
            ...(commonHelpers.isDefined(implicit) && {implicit: `${implicit}`}),
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

        requestStateUpdater(request.name, {
            inProgress: true,
        });

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

    addEntries(
        publisherGroupWithEntries: PublisherGroupWithEntries,
        requestStateUpdater: RequestStateUpdater
    ): Observable<PublisherGroupWithEntries> {
        const request =
            PUBLISHER_GROUPS_CONFIG.requests.publisherGroups.addEntries;

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .post<ApiResponse<PublisherGroupWithEntries>>(
                request.url,
                publisherGroupWithEntries
            )
            .pipe(
                map(response => {
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

    listConnections(
        publisherGroupId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<PublisherGroupConnection[]> {
        const request = replaceUrl(
            PUBLISHER_GROUPS_CONFIG.requests.publisherGroups.listConnections,
            {publisherGroupId: publisherGroupId}
        );

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .get<ApiResponse<PublisherGroupConnection[]>>(request.url)
            .pipe(
                map(response => {
                    requestStateUpdater(request.name, {
                        inProgress: false,
                    });
                    return response.data;
                }),
                catchError((error: HttpErrorResponse) => {
                    requestStateUpdater(request.name, {
                        inProgress: false,
                        error: true,
                        errorMessage: error?.error?.details || error.message,
                    });
                    return throwError(error);
                })
            );
    }

    removeConnection(
        publisherGroupId: string,
        connection: PublisherGroupConnection,
        requestStateUpdater: RequestStateUpdater
    ): Observable<void> {
        const request = replaceUrl(
            PUBLISHER_GROUPS_CONFIG.requests.publisherGroups.removeConnection,
            {
                publisherGroupId: publisherGroupId,
                location: connection.location.toString(),
                entityId: connection.id.toString(),
            }
        );

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .delete<ApiResponse<PublisherGroupConnection>>(request.url)
            .pipe(
                map(() => {
                    requestStateUpdater(request.name, {
                        inProgress: false,
                        error: false,
                        errorMessage: undefined,
                    });
                }),
                catchError((error: HttpErrorResponse) => {
                    requestStateUpdater(request.name, {
                        inProgress: false,
                        error: true,
                        errorMessage: error?.error?.details || error.message,
                    });
                    return throwError(error);
                })
            );
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
