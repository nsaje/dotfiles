import {Injectable, OnDestroy, Inject} from '@angular/core';
import {Store} from 'rxjs-observable-store';
import {takeUntil} from 'rxjs/operators';
import {PublisherGroupsService} from '../../../../core/publisher-groups/services/publisher-groups.service';
import {Observable, Subject} from 'rxjs';
import {RequestStateUpdater} from '../../../../shared/types/request-state-updater';
import {PublisherGroupsStoreState} from './publisher-groups.store.state';
import {PublisherGroup} from '../../../../core/publisher-groups/types/publisher-group';
import {HttpErrorResponse} from '@angular/common/http';
import * as storeHelpers from '../../../../shared/helpers/store.helpers';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import {PublisherGroupFieldsErrorsState} from '../../../publisher-groups/types/publisher-group-fields-errors-state';
import {ChangeEvent} from '../../../../shared/types/change-event';
import {AccountService} from '../../../../core/entities/services/account/account.service';
import {Account} from '../../../../core/entities/types/account/account';
import {ScopeSelectorState} from '../../../../shared/components/scope-selector/scope-selector.constants';
import {PaginationOptions} from '../../../../shared/components/smart-grid/types/pagination-options';
import {PublisherGroupConnection} from '../../../../core/publisher-groups/types/publisher-group-connection';
import {RequestState} from '../../../../shared/types/request-state';
import {AuthStore} from '../../../../core/auth/services/auth.store';

@Injectable()
export class PublisherGroupsStore extends Store<PublisherGroupsStoreState>
    implements OnDestroy {
    private ngUnsubscribe$: Subject<void> = new Subject();
    private requestStateUpdater: RequestStateUpdater;
    private accountsRequestStateUpdater: RequestStateUpdater;

    constructor(
        private publisherGroupsService: PublisherGroupsService,
        private accountsService: AccountService,
        private authStore: AuthStore
    ) {
        super(new PublisherGroupsStoreState());
        this.requestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this
        );
        this.accountsRequestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this,
            'accountsRequests'
        );
    }

    ngOnDestroy() {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    setStore(
        agencyId: string | null,
        accountId: string | null,
        explicitPaginationOptions: PaginationOptions,
        implicitPaginationOptions: PaginationOptions
    ): Promise<void> {
        // If Account ID and Agency ID have changed, reload everything
        if (
            this.state.agencyId !== agencyId ||
            this.state.accountId !== accountId
        ) {
            return new Promise<void>((resolve, reject) => {
                Promise.all([
                    this.loadPublisherGroups(
                        agencyId,
                        accountId,
                        false,
                        explicitPaginationOptions.page,
                        explicitPaginationOptions.pageSize
                    ),
                    this.loadPublisherGroups(
                        agencyId,
                        accountId,
                        true,
                        implicitPaginationOptions.page,
                        implicitPaginationOptions.pageSize
                    ),
                    this.loadAccounts(agencyId),
                ])
                    .then(
                        (
                            values: [
                                PublisherGroup[],
                                PublisherGroup[],
                                Account[]
                            ]
                        ) => {
                            const writableAccounts: Account[] = values[2].filter(
                                account =>
                                    !this.authStore.hasReadOnlyAccessOn(
                                        agencyId,
                                        account.id
                                    )
                            );

                            this.setState({
                                ...this.state,
                                agencyId: agencyId,
                                accountId: accountId,
                                hasAgencyScope: this.authStore.hasAgencyScope(
                                    agencyId
                                ),
                                explicitEntities: values[0],
                                implicitEntities: values[1],
                                explicitPaginationOptions,
                                implicitPaginationOptions,
                                accounts: writableAccounts,
                            });
                            resolve();
                        }
                    )
                    .catch(() => reject());
            });
        }

        // If Account ID and Agency ID are the same as before, only reload grid(s) with changed pagination
        const promises: Promise<void>[] = [];

        if (
            this.isPaginationChanged(
                this.state.explicitPaginationOptions,
                explicitPaginationOptions
            )
        ) {
            promises.push(this.loadEntities(false, explicitPaginationOptions));
        }

        if (
            this.isPaginationChanged(
                this.state.implicitPaginationOptions,
                implicitPaginationOptions
            )
        ) {
            promises.push(this.loadEntities(true, implicitPaginationOptions));
        }

        return new Promise<void>((resolve, reject) => {
            Promise.all(promises)
                .then(x => resolve())
                .catch(() => reject());
        });
    }

    loadEntities(
        implicit: boolean,
        paginationOptions: PaginationOptions
    ): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            this.loadPublisherGroups(
                this.state.agencyId,
                this.state.accountId,
                implicit,
                paginationOptions.page,
                paginationOptions.pageSize
            ).then(
                (publisherGroups: PublisherGroup[]) => {
                    const stateKey = implicit
                        ? 'implicitEntities'
                        : 'explicitEntities';
                    this.patchState(publisherGroups, stateKey);
                    const paginationOptionsKey = implicit
                        ? 'implicitPaginationOptions'
                        : 'explicitPaginationOptions';
                    this.patchState(paginationOptions, paginationOptionsKey);
                    resolve();
                },
                () => {
                    reject();
                }
            );
        });
    }

    setActiveEntity(entity: Partial<PublisherGroup>): void {
        const newActiveEntity = new PublisherGroupsStoreState().activeEntity;
        let scopeState = null;

        if (!commonHelpers.isDefined(entity.id)) {
            if (
                this.state.accountId === null &&
                this.state.hasAgencyScope === true
            ) {
                newActiveEntity.entity.agencyId = this.state.agencyId;
                scopeState = ScopeSelectorState.AGENCY_SCOPE;
            } else {
                newActiveEntity.entity.accountId = this.state.accountId;
                scopeState = ScopeSelectorState.ACCOUNT_SCOPE;
            }
        } else {
            if (commonHelpers.isDefined(entity.agencyId)) {
                scopeState = ScopeSelectorState.AGENCY_SCOPE;
            } else {
                scopeState = ScopeSelectorState.ACCOUNT_SCOPE;
            }
        }

        this.setState({
            ...this.state,
            activeEntity: {
                ...newActiveEntity,
                scopeState: scopeState,
                isReadOnly: this.isReadOnly({
                    ...newActiveEntity.entity,
                    ...entity,
                }),
                entity: {
                    ...newActiveEntity.entity,
                    ...entity,
                },
            },
        });
    }

    setActiveEntityAccount(accountId: string) {
        this.patchState(
            {
                ...this.state.activeEntity.entity,
                accountId: accountId,
            },
            'activeEntity',
            'entity'
        );
    }

    setActiveEntityScope(scopeState: ScopeSelectorState) {
        this.setState({
            ...this.state,
            activeEntity: {
                ...this.state.activeEntity,
                scopeState: scopeState,
                entity: {
                    ...this.state.activeEntity.entity,
                    agencyId:
                        scopeState === ScopeSelectorState.AGENCY_SCOPE
                            ? this.state.agencyId
                            : null,
                    accountId:
                        scopeState === ScopeSelectorState.ACCOUNT_SCOPE
                            ? commonHelpers.getValueOrDefault(
                                  this.state.accountId,
                                  this.state.accounts[0].id
                              )
                            : null,
                },
            },
        });
    }

    saveActiveEntity(): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            this.publisherGroupsService
                .upload(
                    this.state.activeEntity.entity,
                    this.requestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    () => {
                        this.patchState(
                            new PublisherGroupsStoreState().activeEntity.entity,
                            'activeEntity',
                            'entity'
                        );
                        resolve();
                    },
                    (error: HttpErrorResponse) => {
                        const fieldsErrors = storeHelpers.getStoreFieldsErrorsState(
                            new PublisherGroupFieldsErrorsState(),
                            error
                        );
                        if (error.status === 413) {
                            fieldsErrors.entries = ['File too large.'];
                        }
                        this.patchState(
                            fieldsErrors,
                            'activeEntity',
                            'fieldsErrors'
                        );
                        reject();
                    }
                );
        });
    }

    changeActiveEntity(event: ChangeEvent<PublisherGroup>): void {
        this.patchState(
            {...event.target, ...event.changes},
            'activeEntity',
            'entity'
        );
    }

    deleteEntity(publisherGroupId: string): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            this.publisherGroupsService
                .remove(publisherGroupId, this.requestStateUpdater)
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    () => {
                        resolve();
                    },
                    (error: HttpErrorResponse) => {
                        reject(error.error.details);
                    }
                );
        });
    }

    loadActiveEntityConnections(): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            this.publisherGroupsService
                .listConnections(
                    this.state.activeEntity.entity.id,
                    this.requestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    (connections: PublisherGroupConnection[]) => {
                        this.patchState(
                            connections,
                            'activeEntity',
                            'connections'
                        );
                        resolve();
                    },
                    error => {
                        reject();
                    }
                );
        });
    }

    deleteActiveEntityConnection(connection: PublisherGroupConnection) {
        return new Promise<void>((resolve, reject) => {
            this.publisherGroupsService
                .removeConnection(
                    this.state.activeEntity.entity.id,
                    connection,
                    this.requestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    () => {
                        resolve();
                    },
                    error => {
                        reject();
                    }
                );
        });
    }

    clearErrors() {
        const patchedRequests: {[key: string]: RequestState} = {};
        Object.keys(this.state.requests).forEach(requestKey => {
            patchedRequests[requestKey] = {
                ...this.state.requests[requestKey],
                error: false,
                errorMessage: undefined,
            };
        });

        this.patchState(patchedRequests as any, 'requests');
    }

    isReadOnly(publisherGroup: PublisherGroup): boolean {
        return this.authStore.hasReadOnlyAccessOn(
            this.state.agencyId,
            publisherGroup.accountId
        );
    }

    private isPaginationChanged(
        oldPagination: PaginationOptions,
        newPagination: PaginationOptions
    ) {
        if (
            !oldPagination ||
            !newPagination ||
            oldPagination.page !== newPagination.page ||
            oldPagination.pageSize !== newPagination.pageSize
        ) {
            return true;
        } else {
            return false;
        }
    }

    private loadPublisherGroups(
        agencyId: string | null,
        accountId: string | null,
        implicit: boolean,
        page: number,
        pageSize: number
    ): Promise<PublisherGroup[]> {
        return new Promise<PublisherGroup[]>((resolve, reject) => {
            const offset = this.getOffset(page, pageSize);
            const serviceMethod: (
                agencyId: string | null,
                accountId: string | null,
                keyword: string | null,
                offset: number | null,
                limit: number | null,
                requestStateUpdater: RequestStateUpdater
            ) => Observable<PublisherGroup[]> = implicit
                ? this.publisherGroupsService.listImplicit.bind(
                      this.publisherGroupsService
                  )
                : this.publisherGroupsService.listExplicit.bind(
                      this.publisherGroupsService
                  );

            serviceMethod(
                agencyId,
                accountId,
                null,
                offset,
                pageSize,
                this.requestStateUpdater
            )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    (publisherGroups: PublisherGroup[]) => {
                        resolve(publisherGroups);
                    },
                    error => {
                        reject();
                    }
                );
        });
    }

    private loadAccounts(agencyId: string): Promise<Account[]> {
        return new Promise<Account[]>((resolve, reject) => {
            this.accountsService
                .list(
                    agencyId,
                    null,
                    null,
                    null,
                    this.accountsRequestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    accounts => {
                        resolve(accounts);
                    },
                    () => {
                        reject();
                    }
                );
        });
    }

    private getOffset(page: number, pageSize: number): number {
        return (page - 1) * pageSize;
    }
}
