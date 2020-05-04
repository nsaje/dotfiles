import {Injectable, OnDestroy, Inject} from '@angular/core';
import {Store} from 'rxjs-observable-store';
import {takeUntil} from 'rxjs/operators';
import {PublisherGroupsService} from '../../../../core/publisher-groups/services/publisher-groups.service';
import {Subject} from 'rxjs';
import {RequestStateUpdater} from '../../../../shared/types/request-state-updater';
import {PublisherGroupsStoreState} from './publisher-groups.store.state';
import {PublisherGroup} from '../../../../core/publisher-groups/types/publisher-group';
import {HttpErrorResponse} from '@angular/common/http';
import * as storeHelpers from '../../../../shared/helpers/store.helpers';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import {PublisherGroupsStoreFieldsErrorsState} from './publisher-groups.store.fields-errors-state';
import {ChangeEvent} from '../../../../shared/types/change-event';
import {AccountService} from '../../../../core/entities/services/account/account.service';
import {Account} from '../../../../core/entities/types/account/account';
import {ScopeSelectorState} from '../../../../shared/components/scope-selector/scope-selector.constants';

@Injectable()
export class PublisherGroupsStore extends Store<PublisherGroupsStoreState>
    implements OnDestroy {
    private ngUnsubscribe$: Subject<void> = new Subject();
    private requestStateUpdater: RequestStateUpdater;
    private accountsRequestStateUpdater: RequestStateUpdater;

    constructor(
        private publisherGroupsService: PublisherGroupsService,
        private accountsService: AccountService,
        @Inject('zemPermissions') private zemPermissions: any
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

    setStore(
        agencyId: string | null,
        accountId: string | null
    ): Promise<boolean> {
        return new Promise<boolean>(resolve => {
            Promise.all([
                this.loadPublisherGroups(agencyId, accountId),
                this.loadAccounts(agencyId),
            ])
                .then((values: [PublisherGroup[], Account[]]) => {
                    const splitRows: PublisherGroup[][] = this.postProcessLegacyServiceResponse(
                        values[0]
                    );

                    this.setState({
                        ...this.state,
                        agencyId: agencyId,
                        accountId: accountId,
                        hasAgencyScope: this.zemPermissions.hasAgencyScope(
                            agencyId
                        ),
                        entities: splitRows[0],
                        systemEntities: splitRows[1],
                        accounts: values[1],
                    });
                    resolve(true);
                })
                .catch(() => resolve(false));
        });
    }

    loadEntities(): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            this.loadPublisherGroups(
                this.state.agencyId,
                this.state.accountId
            ).then(
                (publisherGroups: PublisherGroup[]) => {
                    const splitRows: PublisherGroup[][] = this.postProcessLegacyServiceResponse(
                        publisherGroups
                    );

                    this.patchState(splitRows[0], 'entities');
                    this.patchState(splitRows[1], 'systemEntities');
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
                            new PublisherGroupsStoreFieldsErrorsState(),
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
                    error => {
                        reject();
                    }
                );
        });
    }

    ngOnDestroy() {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    private loadPublisherGroups(
        agencyId: string | null,
        accountId: string | null
    ): Promise<PublisherGroup[]> {
        return new Promise<PublisherGroup[]>((resolve, reject) => {
            this.publisherGroupsService
                .list(agencyId, accountId, this.requestStateUpdater)
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

    private isReadOnly(publisherGroup: PublisherGroup): boolean {
        if (!this.state.hasAgencyScope && publisherGroup.agencyId) {
            return true;
        } else {
            return false;
        }
    }

    private loadAccounts(agencyId: string): Promise<Account[]> {
        return new Promise<Account[]>((resolve, reject) => {
            this.accountsService
                .list(agencyId, this.accountsRequestStateUpdater)
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

    /*This method is temporary and will be removed after the backend is updated. It simulates some aspects of the new service's responses:
     * - the list of publisher groups is split into user and system publishers*/
    private postProcessLegacyServiceResponse(
        publisherGroups: PublisherGroup[]
    ): PublisherGroup[][] {
        const splitRows: PublisherGroup[][] = [[], []];

        splitRows[0] = publisherGroups.filter(pg => pg.implicit === false);
        splitRows[1] = publisherGroups.filter(pg => pg.implicit === true);

        return splitRows;
    }
}
