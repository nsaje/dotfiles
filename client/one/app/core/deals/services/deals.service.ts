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
        agencyId: string,
        offset: number,
        limit: number,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Deal[]> {
        return this.endpoint.list(agencyId, offset, limit, requestStateUpdater);
    }

    save(
        agencyId: string,
        deal: Deal,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Deal> {
        if (!commonHelpers.isDefined(deal.id)) {
            return this.create(agencyId, deal, requestStateUpdater);
        }
        return this.edit(agencyId, deal, requestStateUpdater);
    }

    validate(
        agencyId: string,
        deal: Partial<Deal>,
        requestStateUpdater: RequestStateUpdater
    ): Observable<void> {
        return this.endpoint.validate(agencyId, deal, requestStateUpdater);
    }

    get(
        agencyId: string,
        dealId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Deal> {
        return this.endpoint.get(agencyId, dealId, requestStateUpdater);
    }

    remove(
        agencyId: string,
        dealId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<void> {
        return this.endpoint.remove(agencyId, dealId, requestStateUpdater);
    }

    listConnections(
        agencyId: string,
        dealId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<DealConnection[]> {
        return this.endpoint.listConnections(
            agencyId,
            dealId,
            requestStateUpdater
        );
    }

    removeConnection(
        agencyId: string,
        dealId: string,
        dealConnectionId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<void> {
        return this.endpoint.removeConnection(
            agencyId,
            dealId,
            dealConnectionId,
            requestStateUpdater
        );
    }

    private create(
        agencyId: string,
        deal: Deal,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Deal> {
        return this.endpoint.create(agencyId, deal, requestStateUpdater);
    }

    private edit(
        agencyId: string,
        deal: Deal,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Deal> {
        return this.endpoint.edit(agencyId, deal, requestStateUpdater);
    }
}
