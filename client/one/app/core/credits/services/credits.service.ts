import {Injectable} from '@angular/core';
import {CreditsEndpoint} from './credits.endpoint';
import {Credit} from '../types/credit';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {Observable} from 'rxjs';
import {isDefined} from '../../../shared/helpers/common.helpers';
import {CampaignBudget} from '../../entities/types/campaign/campaign-budget';
import {CreditRefund} from '../types/credit-refund';
import {CreditTotal} from '../types/credit-total';

@Injectable()
export class CreditsService {
    constructor(private endpoint: CreditsEndpoint) {}

    listActive(
        agencyId: string | null,
        accountId: string | null,
        excludeCanceled: boolean,
        offset: number,
        limit: number,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Credit[]> {
        return this.endpoint.list(
            agencyId,
            accountId,
            true,
            excludeCanceled,
            offset,
            limit,
            requestStateUpdater
        );
    }

    listPast(
        agencyId: string | null,
        accountId: string | null,
        excludeCanceled: boolean,
        offset: number,
        limit: number,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Credit[]> {
        return this.endpoint.list(
            agencyId,
            accountId,
            false,
            excludeCanceled,
            offset,
            limit,
            requestStateUpdater
        );
    }

    save(
        credit: Credit,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Credit> {
        if (!isDefined(credit.id)) {
            return this.endpoint.create(credit, requestStateUpdater);
        }
        return this.endpoint.edit(credit, requestStateUpdater);
    }

    totals(
        agencyId: string | null,
        accountId: string | null,
        requestStateUpdater: RequestStateUpdater
    ): Observable<CreditTotal[]> {
        return this.endpoint.totals(agencyId, accountId, requestStateUpdater);
    }

    listBudgets(
        creditId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<CampaignBudget[]> {
        return this.endpoint.listBudgets(creditId, requestStateUpdater);
    }

    listRefunds(
        creditId: string,
        offset: number,
        limit: number,
        requestStateUpdater: RequestStateUpdater
    ): Observable<CreditRefund[]> {
        return this.endpoint.listRefunds(
            creditId,
            offset,
            limit,
            requestStateUpdater
        );
    }

    createRefund(
        creditId: string,
        creditRefund: CreditRefund,
        requestStateUpdater: RequestStateUpdater
    ): Observable<CreditRefund> {
        return this.endpoint.createRefund(
            creditId,
            creditRefund,
            requestStateUpdater
        );
    }
}
