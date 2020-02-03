import {Injectable} from '@angular/core';
import {RequestStateUpdater} from '../../../../shared/types/request-state-updater';
import {Observable} from 'rxjs';
import {AgencyEndpoint} from './agency.endpoint';
import {Agency} from '../../types/agency/agency';

@Injectable()
export class AgencyService {
    constructor(private endpoint: AgencyEndpoint) {}

    list(requestStateUpdater: RequestStateUpdater): Observable<Agency[]> {
        return this.endpoint.list(requestStateUpdater);
    }
}
