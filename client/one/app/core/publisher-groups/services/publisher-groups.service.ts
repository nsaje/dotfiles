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

    list(
        accountId: string | null,
        requestStateUpdater: RequestStateUpdater
    ): Observable<PublisherGroup[]> {
        return this.endpoint.list(accountId, requestStateUpdater);
    }

    upload(
        publisherGroup: PublisherGroup,
        requestStateUpdater: RequestStateUpdater
    ): Observable<PublisherGroup> {
        return this.endpoint.upload(publisherGroup, requestStateUpdater);
    }

    download(publisherGroup: PublisherGroup) {
        this.endpoint.download(publisherGroup);
    }

    downloadErrors(publisherGroup: PublisherGroup, csvKey: string) {
        this.endpoint.downloadErrors(publisherGroup, csvKey);
    }

    downloadExample() {
        this.endpoint.downloadExample();
    }
}
