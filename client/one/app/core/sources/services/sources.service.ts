import {Injectable} from '@angular/core';
import {SourcesEndpoint} from './sources.endpoint';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {Observable} from 'rxjs';
import {Source} from '../types/source';

@Injectable()
export class SourcesService {
    constructor(private endpoint: SourcesEndpoint) {}

    list(
        agencyId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Source[]> {
        return this.endpoint.list(agencyId, requestStateUpdater);
    }
}
