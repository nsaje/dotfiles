import {Injectable} from '@angular/core';
import {UsersEndpoint} from './users.endpoint';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {Observable} from 'rxjs';
import {User} from '../types/user';

@Injectable()
export class UsersService {
    constructor(private endpoint: UsersEndpoint) {}

    list(
        agencyId: string | null,
        accountId: string | null,
        offset: number | null,
        limit: number | null,
        keyword: string | null,
        showInternal: boolean | null,
        requestStateUpdater: RequestStateUpdater
    ): Observable<User[]> {
        return this.endpoint.list(
            agencyId,
            accountId,
            offset,
            limit,
            keyword,
            showInternal,
            requestStateUpdater
        );
    }

    create(
        users: User[],
        requestStateUpdater: RequestStateUpdater
    ): Observable<User[]> {
        return this.endpoint.create(users, requestStateUpdater);
    }

    edit(
        user: Partial<User>,
        requestStateUpdater: RequestStateUpdater
    ): Observable<User> {
        return this.endpoint.edit(user, requestStateUpdater);
    }

    validate(
        user: Partial<User>,
        requestStateUpdater: RequestStateUpdater
    ): Observable<void> {
        return this.endpoint.validate(user, requestStateUpdater);
    }

    get(
        userId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<User> {
        return this.endpoint.get(userId, requestStateUpdater);
    }

    remove(
        userId: string,
        requestStateUpdater: RequestStateUpdater
    ): Observable<void> {
        return this.endpoint.remove(userId, requestStateUpdater);
    }
}
