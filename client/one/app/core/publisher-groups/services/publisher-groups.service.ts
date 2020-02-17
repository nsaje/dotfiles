import {Injectable} from '@angular/core';
import {PublisherGroupsEndpoint} from './publisher-groups.endpoint';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {Observable} from 'rxjs';
import {PublisherGroup} from '../types/publisher-group';

@Injectable()
export class PublisherGroupsService {
    constructor(private endpoint: PublisherGroupsEndpoint) {}

    search(
        agencyId: string,
        keyword: string | null,
        offset: number | null,
        limit: number | null,
        requestStateUpdater: RequestStateUpdater
    ): Observable<PublisherGroup[]> {
        return this.endpoint.search(
            agencyId,
            keyword,
            offset,
            limit,
            requestStateUpdater
        );
    }
}
