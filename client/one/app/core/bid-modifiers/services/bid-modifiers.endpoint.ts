import {Injectable} from '@angular/core';
import {Observable, throwError} from 'rxjs';
import {HttpClient, HttpErrorResponse} from '@angular/common/http';
import {ApiResponse} from 'one/app/shared/types/api-response';
import {map, catchError} from 'rxjs/operators';
import {BidModifier} from '../types/bid-modifier';
import {BidModifierUploadSummary} from '../types/bid-modifier-upload-summary';
import {RequestStateUpdater} from 'one/app/shared/types/request-state-updater';
import {BID_MODIFIER_CONFIG} from '../bid-modifiers.config';
import {Breakdown} from '../../../app.constants';
import * as commonHelpers from '../../../shared/helpers/common.helpers';

@Injectable()
export class BidModifiersEndpoint {
    constructor(private http: HttpClient) {}

    create(
        adGroupId: number,
        bidModifier: BidModifier,
        requestStateUpdater: RequestStateUpdater
    ): Observable<BidModifier> {
        const request = BID_MODIFIER_CONFIG.requests.save;
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .post<ApiResponse<BidModifier>>(
                `${request.url}${adGroupId}/bidmodifiers/`,
                bidModifier
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
        adGroupId: number,
        bidModifier: BidModifier,
        requestStateUpdater: RequestStateUpdater
    ): Observable<BidModifier> {
        const request = BID_MODIFIER_CONFIG.requests.save;
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .put<ApiResponse<BidModifier>>(
                `${request.url}${adGroupId}/bidmodifiers/${bidModifier.id}`,
                bidModifier
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

    upload(
        adGroupId: number,
        breakdown: Breakdown,
        file: File,
        requestStateUpdater: RequestStateUpdater
    ): Observable<BidModifierUploadSummary> {
        const request = BID_MODIFIER_CONFIG.requests.import;
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        const formData = new FormData();
        formData.append('file', file);

        const url = commonHelpers.isDefined(breakdown)
            ? `${request.url}${adGroupId}/bidmodifiers/upload/${breakdown}/`
            : `${request.url}${adGroupId}/bidmodifiers/upload/`;

        return this.http
            .post<ApiResponse<BidModifierUploadSummary>>(url, formData)
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

    validateUpload(
        adGroupId: number,
        breakdown: Breakdown,
        file: File,
        requestStateUpdater: RequestStateUpdater
    ): Observable<BidModifierUploadSummary> {
        const request = BID_MODIFIER_CONFIG.requests.validateFile;
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        const formData = new FormData();
        formData.append('file', file);

        const baseUrl = commonHelpers.isDefined(adGroupId)
            ? `${request.url}${adGroupId}/`
            : `${request.url}`;
        const url = commonHelpers.isDefined(breakdown)
            ? `${baseUrl}bidmodifiers/validate/${breakdown}/`
            : `${baseUrl}bidmodifiers/validate/`;

        return this.http
            .post<ApiResponse<BidModifierUploadSummary>>(url, formData)
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
