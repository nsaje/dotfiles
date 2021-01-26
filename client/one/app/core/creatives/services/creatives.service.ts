import {Injectable} from '@angular/core';
import {CreativesEndpoint} from './creatives.endpoint';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {Observable} from 'rxjs';
import {Creative} from '../types/creative';
import {AdType} from '../../../app.constants';
import {CreativeBatch} from '../types/creative-batch';

@Injectable()
export class CreativesService {
    constructor(private endpoint: CreativesEndpoint) {}

    list(
        agencyId: string | null,
        accountId: string | null,
        offset: number | null,
        limit: number | null,
        keyword: string | null,
        creativeType: AdType | null,
        tags: string[] | null,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Creative[]> {
        return this.endpoint.list(
            agencyId,
            accountId,
            offset,
            limit,
            keyword,
            creativeType,
            tags,
            requestStateUpdater
        );
    }

    getBatch(
        batchId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<CreativeBatch> {
        return this.endpoint.getBatch(batchId, requestStateUpdater);
    }

    validateBatch(
        batch: Partial<CreativeBatch>,
        requestStateUpdater: RequestStateUpdater
    ): Observable<void> {
        return this.endpoint.validateBatch(batch, requestStateUpdater);
    }

    createBatch(
        batch: CreativeBatch,
        requestStateUpdater: RequestStateUpdater
    ): Observable<CreativeBatch> {
        return this.endpoint.createBatch(batch, requestStateUpdater);
    }

    editBatch(
        batch: CreativeBatch,
        requestStateUpdater: RequestStateUpdater
    ): Observable<CreativeBatch> {
        return this.endpoint.editBatch(batch, requestStateUpdater);
    }
}
