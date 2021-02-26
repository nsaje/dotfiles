import {Injectable} from '@angular/core';
import {Observable} from 'rxjs';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {
    EntityHistoryLevel,
    EntityHistoryOrder,
} from '../entity-history.constants';
import {EntityHistory} from '../types/entity-history';
import {EntityHistoryEndpoint} from './entity-history.endpoint';

@Injectable()
export class EntityHistoryService {
    constructor(private endpoint: EntityHistoryEndpoint) {}

    getHistory(
        entityId: string,
        level: EntityHistoryLevel,
        order: EntityHistoryOrder,
        fromDate: Date,
        requestStateUpdater: RequestStateUpdater
    ): Observable<EntityHistory[]> {
        return this.endpoint.getHistory(
            entityId,
            level,
            order,
            fromDate,
            requestStateUpdater
        );
    }
}
