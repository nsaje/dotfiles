import {Injectable} from '@angular/core';
import {Observable, throwError} from 'rxjs';
import {HttpClient, HttpErrorResponse} from '@angular/common/http';
import {RequestStateUpdater} from 'one/app/shared/types/request-state-updater';
import {catchError, map} from 'rxjs/operators';
import {PublisherTargeting} from '../types/publisher-targeting';
import {PUBLISHERS_CONFIG} from './publishers.config';
import {PublisherTargetingResponse} from '../types/publisher-targeting-response';
import {ApiResponse} from '../../../shared/types/api-response';
import {isPrimitive} from '../../../shared/helpers/common.helpers';

@Injectable()
export class PublishersEndpoint {
    constructor(private http: HttpClient) {}

    updateBlacklistStatuses(
        statusUpdates: PublisherTargeting,
        requestStateUpdater: RequestStateUpdater
    ): Observable<boolean> {
        const request =
            PUBLISHERS_CONFIG.requests.publishers.updateBlacklistStatuses;
        requestStateUpdater(request.name, {
            inProgress: true,
        });
        const snakeCased: any = this.camelObjectToSnakeCase(statusUpdates);

        return this.http
            .post<ApiResponse<PublisherTargetingResponse>>(
                `${request.url}`,
                snakeCased
            )
            .pipe(
                map(response => {
                    requestStateUpdater(request.name, {
                        inProgress: false,
                    });
                    return response.data.success;
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

    /** This is temporary until the backend gets updated */
    camelPropertyToSnakeCase(camelKey: string): string {
        return Array.from(camelKey)
            .map(x => (x === x.toUpperCase() ? '_' + x.toLowerCase() : x))
            .join('');
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
