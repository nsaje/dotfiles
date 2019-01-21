import {Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {AdGroup} from '../types/ad-group';
import {Observable, of} from 'rxjs';

@Injectable()
export class AdGroupEndpoint {
    constructor(private http: HttpClient) {}

    query(id: number): Observable<AdGroup> {
        // TODO (jurebajt): Make actual API call
        return of({id: id, state: 1, archived: false});
    }

    create(adGroup: AdGroup): Observable<AdGroup> {
        // TODO (jurebajt): Make actual API call
        return of(adGroup);
    }

    edit(adGroup: Partial<AdGroup>): Observable<AdGroup> {
        // TODO (jurebajt): Make actual API call
        return of(adGroup as AdGroup);
    }
}
