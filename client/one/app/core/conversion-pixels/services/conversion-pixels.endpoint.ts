import {Injectable} from '@angular/core';
import {HttpClient, HttpErrorResponse} from '@angular/common/http';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {Observable, throwError} from 'rxjs';
import {ApiResponse} from '../../../shared/types/api-response';
import {map, catchError} from 'rxjs/operators';
import {ConversionPixel} from '../types/conversion-pixel';
import {CONVERSION_PIXELS_CONFIG} from '../conversion-pixels.config';

@Injectable()
export class ConversionPixelsEndpoint {
    constructor(private http: HttpClient) {}

    list(
        accountId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<ConversionPixel[]> {
        const request = CONVERSION_PIXELS_CONFIG.requests.conversionPixels.list;

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .get<ApiResponse<ConversionPixel[]>>(
                `${request.url}${accountId}/pixels/`
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

    create(
        accountId: string,
        conversionPixelName: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<ConversionPixel> {
        const request =
            CONVERSION_PIXELS_CONFIG.requests.conversionPixels.create;
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .post<ApiResponse<ConversionPixel>>(
                `${request.url}${accountId}/pixels/`,
                {name: conversionPixelName}
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

    edit(
        conversionPixel: ConversionPixel,
        requestStateUpdater: RequestStateUpdater
    ): Observable<ConversionPixel> {
        const request = CONVERSION_PIXELS_CONFIG.requests.conversionPixels.edit;
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .put<ApiResponse<ConversionPixel>>(
                `${request.url}${conversionPixel.accountId}/pixels/${conversionPixel.id}`,
                conversionPixel
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
}
