import {Injectable, OnDestroy, Inject} from '@angular/core';
import {HttpErrorResponse} from '@angular/common/http';
import {Subject} from 'rxjs';
import {Store} from 'rxjs-observable-store';
import {takeUntil} from 'rxjs/operators';
import {ChangeEvent} from '../../../../shared/types/change-event';
import {Deal} from '../../../../core/deals/types/deal';
import {DealConnection} from '../../../../core/deals/types/deal-connection';
import {DealsLibraryStoreState} from './deals-library.store.state';
import {DealsLibraryStoreFieldsErrorsState} from './deals-library.store.fields-errors-state';
import {DealsService} from '../../../../core/deals/services/deals.service';
import {SourcesService} from '../../../../core/sources/services/sources.service';
import {RequestStateUpdater} from '../../../../shared/types/request-state-updater';
import * as storeHelpers from '../../../../shared/helpers/store.helpers';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import {AccountService} from '../../../../core/entities/services/account/account.service';
import {Account} from '../../../../core/entities/types/account/account';
import {Source} from '../../../../core/sources/types/source';
import {ScopeSelectorState} from '../../../../shared/components/scope-selector/scope-selector.constants';

@Injectable()
export class DealsLibraryStore extends Store<DealsLibraryStoreState>
    implements OnDestroy {
    private ngUnsubscribe$: Subject<void> = new Subject();
    private requestStateUpdater: RequestStateUpdater;
    private sourcesRequestStateUpdater: RequestStateUpdater;
    private accountsRequestStateUpdater: RequestStateUpdater;

    constructor(
        private dealsService: DealsService,
        private sourcesService: SourcesService,
        private accountsService: AccountService,
        @Inject('zemPermissions') private zemPermissions: any
    ) {
        super(new DealsLibraryStoreState());
        this.requestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this
        );
        this.sourcesRequestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this,
            'sourcesRequests'
        );
        this.accountsRequestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this,
            'accountsRequests'
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
            Promise.all([
                this.loadDeals(agencyId, accountId, page, pageSize, keyword),
                this.loadSources(agencyId),
                this.loadAccounts(agencyId),
            ])
                .then((values: [Deal[], Source[], Account[]]) => {
                    this.setState({
                        ...this.state,
                        agencyId: agencyId,
                        accountId: accountId,
                        hasAgencyScope: this.zemPermissions.hasAgencyScope(
                            agencyId
                        ),
                        entities: values[0],
                        sources: values[1],
                        accounts: values[2],
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
            this.loadDeals(
                this.state.agencyId,
                this.state.accountId,
                page,
                pageSize,
                keyword
            ).then(
                (deals: Deal[]) => {
                    this.patchState(deals, 'entities');
                    resolve();
                },
                () => {
                    reject();
                }
            );
        });
    }

    saveActiveEntity(): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            this.dealsService
                .save(this.state.activeEntity.entity, this.requestStateUpdater)
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    () => {
                        this.patchState(
                            new DealsLibraryStoreState().activeEntity.entity,
                            'activeEntity',
                            'entity'
                        );
                        resolve();
                    },
                    (error: HttpErrorResponse) => {
                        const fieldsErrors = storeHelpers.getStoreFieldsErrorsState(
                            new DealsLibraryStoreFieldsErrorsState(),
                            error
                        );
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

    validateActiveEntity(): void {
        const entity = storeHelpers.getNewStateWithoutNull(
            this.state.activeEntity.entity
        );
        this.dealsService
            .validate(entity, this.requestStateUpdater)
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe(
                () => {
                    this.patchState(
                        new DealsLibraryStoreFieldsErrorsState(),
                        'activeEntity',
                        'fieldsErrors'
                    );
                },
                (error: HttpErrorResponse) => {
                    const fieldsErrors = storeHelpers.getStoreFieldsErrorsState(
                        new DealsLibraryStoreFieldsErrorsState(),
                        error
                    );
                    this.patchState(
                        fieldsErrors,
                        'activeEntity',
                        'fieldsErrors'
                    );
                }
            );
    }

    deleteEntity(dealId: string): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            this.dealsService
                .remove(dealId, this.requestStateUpdater)
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

    loadActiveEntityConnections(): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            this.dealsService
                .listConnections(
                    this.state.activeEntity.entity.id,
                    this.requestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    (connections: DealConnection[]) => {
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

    deleteActiveEntityConnection(dealConnectionId: string) {
        return new Promise<void>((resolve, reject) => {
            this.dealsService
                .removeConnection(
                    this.state.activeEntity.entity.id,
                    dealConnectionId,
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

    setActiveEntity(entity: Partial<Deal>): void {
        const newActiveEntity = new DealsLibraryStoreState().activeEntity;
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
                isReadOnly: this.isDealReadOnly({
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

    changeActiveEntity(event: ChangeEvent<Deal>): void {
        this.patchState(
            {...event.target, ...event.changes},
            'activeEntity',
            'entity'
        );
        this.validateActiveEntity();
    }

    ngOnDestroy() {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    private isDealReadOnly(deal: Deal): boolean {
        if (!this.state.hasAgencyScope && deal.agencyId) {
            return true;
        } else {
            return false;
        }
    }

    private loadDeals(
        agencyId: string | null,
        accountId: string | null,
        page: number,
        pageSize: number,
        keyword: string | null = null
    ): Promise<Deal[]> {
        return new Promise<Deal[]>((resolve, reject) => {
            const offset = this.getOffset(page, pageSize);
            this.dealsService
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
                    (deals: Deal[]) => {
                        resolve(deals);
                    },
                    error => {
                        reject();
                    }
                );
        });
    }

    private loadSources(agencyId: string): Promise<Source[]> {
        return new Promise<Source[]>((resolve, reject) => {
            this.sourcesService
                .list(agencyId, this.sourcesRequestStateUpdater)
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    sources => {
                        resolve(sources);
                    },
                    () => {
                        reject();
                    }
                );
        });
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

    private getOffset(page: number, pageSize: number): number {
        return (page - 1) * pageSize;
    }
}
