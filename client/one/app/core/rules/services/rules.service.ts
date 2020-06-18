import {RulesEndpoint} from './rules.endpoint';
import {Injectable} from '@angular/core';
import {Rule} from '../types/rule';
import {Observable} from 'rxjs/internal/Observable';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import * as commonHelpers from '../../../shared/helpers/common.helpers';
import {RuleHistory} from '../types/rule-history';

@Injectable()
export class RulesService {
    constructor(private endpoint: RulesEndpoint) {}

    list(
        agencyId: string | null,
        accountId: string | null,
        offset: number | null,
        limit: number | null,
        agencyOnly: boolean | null,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Rule[]> {
        return this.endpoint.list(
            agencyId,
            accountId,
            offset,
            limit,
            agencyOnly,
            requestStateUpdater
        );
    }

    save(
        rule: Rule,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Rule> {
        if (!commonHelpers.isDefined(rule.id)) {
            return this.create(rule, requestStateUpdater);
        }
        return this.edit(rule, requestStateUpdater);
    }

    get(
        ruleId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Rule> {
        return this.endpoint.get(ruleId, requestStateUpdater);
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
        return this.endpoint.listHistories(
            agencyId,
            accountId,
            offset,
            limit,
            ruleId,
            adGroupId,
            startDate,
            endDate,
            requestStateUpdater
        );
    }

    private create(
        rule: Rule,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Rule> {
        return this.endpoint.create(rule, requestStateUpdater);
    }

    private edit(
        rule: Rule,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Rule> {
        return this.endpoint.edit(rule, requestStateUpdater);
    }
}
