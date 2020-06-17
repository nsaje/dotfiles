import {Injectable, OnDestroy, Inject} from '@angular/core';
import {Subject} from 'rxjs';
import {Store} from 'rxjs-observable-store';
import {takeUntil} from 'rxjs/operators';
import {User} from '../../../../core/users/types/user';
import {UsersStoreState} from './users.store.state';
import {UsersService} from '../../../../core/users/services/users.service';
import {RequestStateUpdater} from '../../../../shared/types/request-state-updater';
import * as storeHelpers from '../../../../shared/helpers/store.helpers';

@Injectable()
export class UsersStore extends Store<UsersStoreState> implements OnDestroy {
    private ngUnsubscribe$: Subject<void> = new Subject();
    private requestStateUpdater: RequestStateUpdater;

    constructor(
        private usersService: UsersService,
        @Inject('zemPermissions') private zemPermissions: any
    ) {
        super(new UsersStoreState());
        this.requestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this
        );
    }

    setStore(
        agencyId: string | null,
        accountId: string | null,
        page: number,
        pageSize: number,
        keyword: string | null
    ): Promise<boolean> {
        return new Promise<boolean>(resolve => {
            this.loadUsers(agencyId, accountId, page, pageSize, keyword)
                .then((values: User[]) => {
                    this.setState({
                        ...this.state,
                        agencyId: agencyId,
                        accountId: accountId,
                        hasAgencyScope: this.zemPermissions.hasAgencyScope(
                            agencyId
                        ),
                        entities: values,
                    });
                    resolve(true);
                })
                .catch(() => resolve(false));
        });
    }

    loadEntities(
        page: number,
        pageSize: number,
        keyword: string | null = null
    ): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            this.loadUsers(
                this.state.agencyId,
                this.state.accountId,
                page,
                pageSize,
                keyword
            ).then(
                (users: User[]) => {
                    this.patchState(users, 'entities');
                    resolve();
                },
                () => {
                    reject();
                }
            );
        });
    }

    ngOnDestroy() {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    private loadUsers(
        agencyId: string | null,
        accountId: string | null,
        page: number,
        pageSize: number,
        keyword: string | null = null
    ): Promise<User[]> {
        return new Promise<User[]>((resolve, reject) => {
            const offset = this.getOffset(page, pageSize);
            this.usersService
                .list(
                    agencyId,
                    accountId,
                    offset,
                    pageSize,
                    keyword,
                    null,
                    this.requestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    (users: User[]) => {
                        resolve(users);
                    },
                    error => {
                        reject();
                    }
                );
        });
    }

    private getOffset(page: number, pageSize: number): number {
        return (page - 1) * pageSize;
    }
}
