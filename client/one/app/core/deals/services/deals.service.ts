import {Injectable} from '@angular/core';
import {DealsEndpoint} from './deals.endpoint';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {Observable} from 'rxjs';
import {Deal} from '../types/deal';
import {DealConnection} from '../types/deal-connection';
import * as commonHelpers from '../../../shared/helpers/common.helpers';

@Injectable()
export class DealsService {
    constructor(private endpoint: DealsEndpoint) {}

    list(
        agencyId: string | null,
        accountId: string | null,
        offset: number | null,
        limit: number | null,
        keyword: string | null,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Deal[]> {
        return this.endpoint.list(
            agencyId,
            accountId,
            offset,
            limit,
            keyword,
            requestStateUpdater
        );
    }

    save(
        deal: Deal,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Deal> {
        if (!commonHelpers.isDefined(deal.id)) {
            return this.create(deal, requestStateUpdater);
        }
        return this.edit(deal, requestStateUpdater);
    }

    validate(
        deal: Partial<Deal>,
        requestStateUpdater: RequestStateUpdater
    ): Observable<void> {
        return this.endpoint.validate(deal, requestStateUpdater);
    }

    get(
        dealId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Deal> {
        return this.endpoint.get(dealId, requestStateUpdater);
    }

    remove(
        dealId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<void> {
        return this.endpoint.remove(dealId, requestStateUpdater);
    }

    listConnections(
        dealId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<DealConnection[]> {
        return this.endpoint.listConnections(dealId, requestStateUpdater);
    }

    removeConnection(
        dealId: string,
        dealConnectionId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<void> {
        return this.endpoint.removeConnection(
            dealId,
            dealConnectionId,
            requestStateUpdater
        );
    }

    private create(
        deal: Deal,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Deal> {
        return this.endpoint.create(deal, requestStateUpdater);
    }

    private edit(
        deal: Deal,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Deal> {
        return this.endpoint.edit(deal, requestStateUpdater);
    }
}
