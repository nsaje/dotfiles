import {Injectable} from '@angular/core';
import {Observable, throwError} from 'rxjs';
import {HttpClient, HttpErrorResponse} from '@angular/common/http';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {EntityHistory} from '../types/entity-history';
import {ENTITY_HISTORY_CONFIG} from '../entity-history.config';
import {ApiResponse} from '../../../shared/types/api-response';
import * as commonHelpers from '../../../shared/helpers/common.helpers';
import * as dateHelpers from '../../../shared/helpers/date.helpers';
import {map, catchError} from 'rxjs/operators';
import {
    EntityHistoryLevel,
    EntityHistoryOrder,
} from '../entity-history.constants';

@Injectable()
export class EntityHistoryEndpoint {
    constructor(private http: HttpClient) {}

    getHistory(
        entityId: string,
        level: EntityHistoryLevel,
        order: EntityHistoryOrder,
        fromDate: Date,
        requestStateUpdater: RequestStateUpdater
    ): Observable<EntityHistory[]> {
        const request = ENTITY_HISTORY_CONFIG.requests.history;

        const params = {
            ...this.getEntityParam(entityId, level),
            level: level,
            order: order,
            ...(commonHelpers.isDefined(fromDate) && {
                fromDate: dateHelpers.convertDateToUTCString(fromDate),
            }),
        };

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .get<ApiResponse<EntityHistory[]>>(request.url, {params: params})
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

    private getEntityParam(entityId: string, level: EntityHistoryLevel) {
        const entityLevelMapping = {
            [EntityHistoryLevel.AD_GROUP]: 'ad_group_id',
            [EntityHistoryLevel.CAMPAIGN]: 'campaign_id',
            [EntityHistoryLevel.ACCOUNT]: 'account_id',
            [EntityHistoryLevel.AGENCY]: 'agency_id',
        };

        return {
            [entityLevelMapping[level]]: entityId,
        };
    }
}
