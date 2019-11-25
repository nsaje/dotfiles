import {RulesEndpoint} from './rules.endpoint';
import {Injectable} from '@angular/core';
import {Rule} from '../types/rule';
import {Observable} from 'rxjs/internal/Observable';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';

@Injectable()
export class RulesService {
    constructor(private endpoint: RulesEndpoint) {}

    save(
        agencyId: string,
        rule: Rule,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Rule> {
        // TODO: add support for update based on id
        return this.endpoint.create(agencyId, rule, requestStateUpdater);
    }
}
