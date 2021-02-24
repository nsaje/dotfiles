import {Injectable} from '@angular/core';
import {CreativesEndpoint} from './creatives.endpoint';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {Observable} from 'rxjs';
import {Creative} from '../types/creative';
import {AdType} from '../../../app.constants';
import {CreativeBatch} from '../types/creative-batch';
import {CreativeCandidate} from '../types/creative-candidate';

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

    listCandidates(
        batchId: string,
        offset: number | null,
        limit: number | null,
        requestStateUpdater: RequestStateUpdater
    ): Observable<CreativeCandidate[]> {
        return this.endpoint.listCandidates(
            batchId,
            offset,
            limit,
            requestStateUpdater
        );
    }

    createCandidate(
        batchId: string,
        candidate: CreativeCandidate,
        requestStateUpdater: RequestStateUpdater
    ): Observable<CreativeCandidate> {
        return this.endpoint.createCandidate(
            batchId,
            candidate,
            requestStateUpdater
        );
    }

    getCandidate(
        batchId: string,
        candidateId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<CreativeCandidate> {
        return this.endpoint.getCandidate(
            batchId,
            candidateId,
            requestStateUpdater
        );
    }

    editCandidate(
        batchId: string,
        candidateId: string,
        changes: Partial<CreativeCandidate>,
        requestStateUpdater: RequestStateUpdater
    ): Observable<CreativeCandidate> {
        return this.endpoint.editCandidate(
            batchId,
            candidateId,
            changes,
            requestStateUpdater
        );
    }

    removeCandidate(
        batchId: string,
        candidateId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<void> {
        return this.endpoint.removeCandidate(
            batchId,
            candidateId,
            requestStateUpdater
        );
    }
}
