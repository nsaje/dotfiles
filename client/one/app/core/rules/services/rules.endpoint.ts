import {Injectable} from '@angular/core';
import {Observable, throwError} from 'rxjs';
import {Rule} from '../types/rule';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {HttpClient, HttpErrorResponse} from '@angular/common/http';
import {ApiResponse} from '../../../shared/types/api-response';
import {map, catchError} from 'rxjs/operators';
import {RULES_CONFIG} from '../rules.config';
import * as commonHelpers from '../../../shared/helpers/common.helpers';
import * as endpointHelpers from '../../../shared/helpers/endpoint.helpers';
import {RuleHistory} from '../types/rule-history';
import {convertDateToString} from '../../../shared/helpers/date.helpers';

@Injectable()
export class RulesEndpoint {
    constructor(private http: HttpClient) {}

    get(
        ruleId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Rule> {
        const request = endpointHelpers.replaceUrl(
            RULES_CONFIG.requests.rules.get,
            {ruleId: ruleId}
        );

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http.get<ApiResponse<Rule>>(request.url).pipe(
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

    list(
        agencyId: string | null,
        accountId: string | null,
        offset: number | null,
        limit: number | null,
        keyword: string | null,
        agencyOnly: boolean | null,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Rule[]> {
        const request = RULES_CONFIG.requests.rules.list;
        const params = {
            offset: `${offset}`,
            limit: `${limit}`,
            ...(commonHelpers.isDefined(agencyId) && {agencyId}),
            ...(commonHelpers.isDefined(accountId) && {accountId}),
            ...(commonHelpers.isDefined(keyword) && {keyword}),
            ...(commonHelpers.isDefined(agencyOnly) && {
                agencyOnly: `${agencyOnly}`,
            }),
        };

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .get<ApiResponse<Rule[]>>(request.url, {params})
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

    create(
        rule: Partial<Rule>,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Rule> {
        const request = RULES_CONFIG.requests.rules.create;
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http.post<ApiResponse<Rule>>(request.url, rule).pipe(
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
        rule: Partial<Rule>,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Rule> {
        const request = endpointHelpers.replaceUrl(
            RULES_CONFIG.requests.rules.edit,
            {ruleId: rule.id}
        );
        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http.put<ApiResponse<Rule>>(request.url, rule).pipe(
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

    listHistories(
        agencyId: string | null,
        accountId: string | null,
        offset: number | null,
        limit: number | null,
        ruleId: string | null,
        adGroupId: string | null,
        startDate: Date | null,
        endDate: Date | null,
        requestStateUpdater: RequestStateUpdater
    ): Observable<RuleHistory[]> {
        const request = RULES_CONFIG.requests.rules.listHistories;
        const params = {
            offset: `${offset}`,
            limit: `${limit}`,
            ...(commonHelpers.isDefined(agencyId) && {agencyId}),
            ...(commonHelpers.isDefined(accountId) && {accountId}),
            ...(commonHelpers.isDefined(ruleId) && {ruleId}),
            ...(commonHelpers.isDefined(adGroupId) && {adGroupId}),
            ...(commonHelpers.isDefined(startDate) && {
                startDate: convertDateToString(startDate),
            }),
            ...(commonHelpers.isDefined(endDate) && {
                endDate: convertDateToString(endDate),
            }),
        };

        requestStateUpdater(request.name, {
            inProgress: true,
        });

        return this.http
            .get<ApiResponse<RuleHistory[]>>(request.url, {params})
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
}
