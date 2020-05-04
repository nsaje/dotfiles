import {Injectable} from '@angular/core';
import {PublisherGroupsEndpoint} from './publisher-groups.endpoint';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {Observable} from 'rxjs';
import {PublisherGroup} from '../types/publisher-group';

@Injectable()
export class PublisherGroupsService {
    constructor(private endpoint: PublisherGroupsEndpoint) {}

    search(
        agencyId: string | null,
        accountId: string | null,
        keyword: string | null,
        offset: number | null,
        limit: number | null,
        includeImplicit: boolean,
        requestStateUpdater: RequestStateUpdater
    ): Observable<PublisherGroup[]> {
        return this.endpoint.search(
            agencyId,
            accountId,
            keyword,
            offset,
            limit,
            includeImplicit,
            requestStateUpdater
        );
    }

    list(
        agencyId: string | null,
        accountId: string | null,
        requestStateUpdater: RequestStateUpdater
    ): Observable<PublisherGroup[]> {
        return this.endpoint.list(agencyId, accountId, requestStateUpdater);
    }

    upload(
        publisherGroup: PublisherGroup,
        requestStateUpdater: RequestStateUpdater
    ): Observable<PublisherGroup> {
        return this.endpoint.upload(publisherGroup, requestStateUpdater);
    }

    remove(
        publisherGroupId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<void> {
        return this.endpoint.remove(publisherGroupId, requestStateUpdater);
    }

    download(publisherGroupId: string) {
        this.endpoint.download(publisherGroupId);
    }

    downloadErrors(publisherGroup: PublisherGroup, csvKey: string) {
        this.endpoint.downloadErrors(publisherGroup, csvKey);
    }

    downloadExample() {
        this.endpoint.downloadExample();
    }
}
