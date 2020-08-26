import {RulesEndpoint} from './rules.endpoint';
import {Injectable} from '@angular/core';
import {Rule} from '../types/rule';
import {Observable} from 'rxjs/internal/Observable';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import * as commonHelpers from '../../../shared/helpers/common.helpers';
import {RuleHistory} from '../types/rule-history';
import {RuleState} from '../rules.constants';

@Injectable()
export class RulesService {
    constructor(private endpoint: RulesEndpoint) {}

    list(
        agencyId: string | null,
        accountId: string | null,
        offset: number | null,
        limit: number | null,
        keyword: string | null,
        agencyOnly: boolean | null,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Rule[]> {
        return this.endpoint.list(
            agencyId,
            accountId,
            offset,
            limit,
            keyword,
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

    archive(
        ruleId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Rule> {
        return this.edit({id: ruleId, archived: true}, requestStateUpdater);
    }

    enable(
        ruleId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Rule> {
        return this.edit(
            {id: ruleId, state: RuleState.ENABLED},
            requestStateUpdater
        );
    }

    pause(
        ruleId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Rule> {
        return this.edit(
            {id: ruleId, state: RuleState.PAUSED},
            requestStateUpdater
        );
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
        showEntriesWithoutChanges: boolean | null,
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
            showEntriesWithoutChanges,
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
        rule: Partial<Rule>,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Rule> {
        return this.endpoint.edit(rule, requestStateUpdater);
    }
}
