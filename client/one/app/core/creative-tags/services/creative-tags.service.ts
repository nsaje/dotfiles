import {Injectable} from '@angular/core';
import {CreativeTagsEndpoint} from './creative-tags.endpoint';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {Observable} from 'rxjs';

@Injectable()
export class CreativeTagsService {
    constructor(private endpoint: CreativeTagsEndpoint) {}

    list(
        agencyId: string | null,
        accountId: string | null,
        offset: number | null,
        limit: number | null,
        keyword: string | null,
        requestStateUpdater: RequestStateUpdater
    ): Observable<string[]> {
        return this.endpoint.list(
            agencyId,
            accountId,
            offset,
            limit,
            keyword,
            requestStateUpdater
        );
    }
}
