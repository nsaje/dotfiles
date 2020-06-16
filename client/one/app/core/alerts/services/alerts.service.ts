import {Injectable} from '@angular/core';
import {AlertsEndpoint} from './alerts.endpoint';
import {Observable, of} from 'rxjs';
import {Level, Breakdown} from '../../../app.constants';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {Alert} from '../types/alert';

@Injectable()
export class AlertsService {
    constructor(private endpoint: AlertsEndpoint) {}

    list(
        level: Level,
        entityId: string | null,
        breakdown: Breakdown | null,
        startDate: Date | null,
        endDate: Date | null,
        requestStateUpdater: RequestStateUpdater
    ): Observable<Alert[]> {
        return this.endpoint.list(
            level,
            entityId,
            breakdown,
            startDate,
            endDate,
            requestStateUpdater
        );
    }
}
