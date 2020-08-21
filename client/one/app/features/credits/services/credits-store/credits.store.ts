import {Injectable, OnDestroy, Inject} from '@angular/core';
import {HttpErrorResponse} from '@angular/common/http';
import {Subject, Observable} from 'rxjs';
import {Store} from 'rxjs-observable-store';
import {takeUntil} from 'rxjs/operators';
import {ChangeEvent} from '../../../../shared/types/change-event';
import {Credit} from '../../../../core/credits/types/credit';
import {CreditRefund} from '../../../../core/credits/types/credit-refund';
import {CreditTotal} from '../../../../core/credits/types/credit-total';
import {CampaignBudget} from '../../../../core/entities/types/campaign/campaign-budget';
import {Account} from '../../../../core/entities/types/account/account';
import {CreditsStoreState} from './credits.store.state';
import {CreditsService} from '../../../../core/credits/services/credits.service';
import {RequestStateUpdater} from '../../../../shared/types/request-state-updater';
import * as storeHelpers from '../../../../shared/helpers/store.helpers';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import * as arrayHelpers from '../../../../shared/helpers/array.helpers';
import {ScopeSelectorState} from '../../../../shared/components/scope-selector/scope-selector.constants';
import {PaginationOptions} from '../../../../shared/components/smart-grid/types/pagination-options';
import {AccountService} from '../../../../core/entities/services/account/account.service';
import {CreditsStoreFieldsErrorsState} from './credits.store.fields-errors-state';
import {CreditStatus, Currency} from '../../../../app.constants';
import {AuthStore} from '../../../../core/auth/services/auth.store';

@Injectable()
export class CreditsStore extends Store<CreditsStoreState>
    implements OnDestroy {
    private ngUnsubscribe$: Subject<void> = new Subject();
    private requestStateUpdater: RequestStateUpdater;
    private accountsRequestStateUpdater: RequestStateUpdater;

    constructor(
        private creditsService: CreditsService,
        private accountsService: AccountService,
        private authStore: AuthStore
    ) {
        super(new CreditsStoreState());
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
        accountId: string | null,
        activePaginationOptions: PaginationOptions,
        pastPaginationOptions: PaginationOptions
    ): Promise<void> {
        if (
            agencyId !== this.state.agencyId ||
            accountId !== this.state.accountId
        ) {
            return new Promise<void>((resolve, reject) => {
                Promise.all([
                    this.loadTotals(agencyId, accountId),
                    this.loadCredits(
                        agencyId,
                        accountId,
                        true,
                        activePaginationOptions.page,
                        activePaginationOptions.pageSize
                    ),
                    this.loadCredits(
                        agencyId,
                        accountId,
                        false,
                        pastPaginationOptions.page,
                        pastPaginationOptions.pageSize
                    ),
                    this.loadAccounts(agencyId),
                ])
                    .then(
                        (
                            values: [
                                CreditTotal[],
                                Credit[],
                                Credit[],
                                Account[]
                            ]
                        ) => {
                            const writableAccounts: Account[] = values[3].filter(
                                account =>
                                    !this.authStore.hasReadOnlyAccess(
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
                                totals: values[0],
                                activeCredits: values[1],
                                pastCredits: values[2],
                                accounts: writableAccounts,
                                activePaginationOptions: activePaginationOptions,
                                pastPaginationOptions: pastPaginationOptions,
                            });
                            resolve();
                        }
                    )
                    .catch(() => reject());
            });
        }

        const promises: Promise<void>[] = [];

        if (
            this.isPaginationChanged(
                this.state.activePaginationOptions,
                activePaginationOptions
            )
        ) {
            promises.push(this.loadEntities(true, activePaginationOptions));
        }

        if (
            this.isPaginationChanged(
                this.state.pastPaginationOptions,
                pastPaginationOptions
            )
        ) {
            promises.push(this.loadEntities(false, pastPaginationOptions));
        }

        return new Promise<void>((resolve, reject) => {
            Promise.all(promises)
                .then(x => resolve())
                .catch(() => reject());
        });
    }

    loadEntities(
        active: boolean,
        paginationOptions: PaginationOptions
    ): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            this.loadCredits(
                this.state.agencyId,
                this.state.accountId,
                active,
                paginationOptions.page,
                paginationOptions.pageSize
            ).then(
                (credits: Credit[]) => {
                    if (active) {
                        this.setState({
                            ...this.state,
                            activeCredits: credits,
                            activePaginationOptions: paginationOptions,
                        });
                    } else {
                        this.setState({
                            ...this.state,
                            pastCredits: credits,
                            pastPaginationOptions: paginationOptions,
                        });
                    }
                    resolve();
                },
                () => {
                    reject();
                }
            );
        });
    }

    loadRefunds(
        creditId: string,
        paginationOptions: PaginationOptions
    ): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            const offset = this.getOffset(
                paginationOptions.page,
                paginationOptions.pageSize
            );
            this.creditsService
                .listRefunds(
                    creditId,
                    offset,
                    paginationOptions.pageSize,
                    this.requestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    refunds => {
                        this.patchState(refunds, 'creditRefunds');
                        resolve();
                    },
                    () => {
                        reject();
                    }
                );
        });
    }

    saveCreditActiveEntity(): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            this.creditsService
                .save(
                    this.state.creditActiveEntity.entity,
                    this.requestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    () => {
                        this.patchState(
                            new CreditsStoreState().creditActiveEntity.entity,
                            'creditActiveEntity',
                            'entity'
                        );
                        resolve();
                    },
                    (error: HttpErrorResponse) => {
                        const fieldsErrors = storeHelpers.getStoreFieldsErrorsState(
                            new CreditsStoreFieldsErrorsState(),
                            error
                        );
                        this.patchState(
                            fieldsErrors,
                            'creditActiveEntity',
                            'fieldsErrors'
                        );
                        reject();
                    }
                );
        });
    }

    cancelCreditActiveEntity(): Promise<void> {
        if (!commonHelpers.isDefined(this.state.creditActiveEntity.entity.id)) {
            return new Promise<void>(reject => reject());
        }

        this.patchState(
            CreditStatus.CANCELED,
            'creditActiveEntity',
            'entity',
            'status'
        );
        return this.saveCreditActiveEntity();
    }

    loadCreditActiveEntityBudgets(): Promise<void> {
        if (!commonHelpers.isDefined(this.state.creditActiveEntity.entity.id)) {
            return new Promise<void>(reject => reject());
        }

        return new Promise<void>((resolve, reject) => {
            this.creditsService
                .listBudgets(
                    this.state.creditActiveEntity.entity.id,
                    this.requestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    (campaignBudgets: CampaignBudget[]) => {
                        this.patchState(
                            campaignBudgets,
                            'creditActiveEntity',
                            'campaignBudgets'
                        );
                        resolve();
                    },
                    error => {
                        reject();
                    }
                );
        });
    }

    setCreditActiveEntity(entity: Partial<Credit>): void {
        const newActiveEntity = new CreditsStoreState().creditActiveEntity;
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
            creditActiveEntity: {
                ...newActiveEntity,
                scopeState: scopeState,
                isReadOnly: this.isReadOnly({
                    ...newActiveEntity.entity,
                    ...entity,
                }),
                isSigned: this.isSigned({
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

    setCreditActiveEntityAccount(accountId: string): void {
        this.patchState(accountId, 'creditActiveEntity', 'entity', 'accountId');
    }

    setCreditActiveEntityScope(scopeState: ScopeSelectorState): void {
        this.setState({
            ...this.state,
            creditActiveEntity: {
                ...this.state.creditActiveEntity,
                scopeState: scopeState,
                entity: {
                    ...this.state.creditActiveEntity.entity,
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

    changeCreditActiveEntity(event: ChangeEvent<Credit>): void {
        this.setState({
            ...this.state,
            creditActiveEntity: {
                ...this.state.creditActiveEntity,
                isSigned: this.isSigned({
                    ...event.target,
                    ...event.changes,
                }),
                entity: {
                    ...event.target,
                    ...event.changes,
                },
            },
        });
    }

    setCreditRefundActiveEntity(entity: Partial<CreditRefund>): void {
        const newActiveEntity = new CreditsStoreState()
            .creditRefundActiveEntity;

        this.setState({
            ...this.state,
            creditRefundActiveEntity: {
                ...newActiveEntity,
                entity: {
                    ...newActiveEntity.entity,
                    ...entity,
                },
            },
        });
    }

    saveCreditRefundActiveEntity(): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            this.creditsService
                .createRefund(
                    this.state.creditActiveEntity.entity.id,
                    this.state.creditRefundActiveEntity.entity,
                    this.requestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    () => {
                        this.patchState(
                            new CreditsStoreState().creditRefundActiveEntity
                                .entity,
                            'creditRefundActiveEntity',
                            'entity'
                        );
                        resolve();
                    },
                    (error: HttpErrorResponse) => {
                        const fieldsErrors = storeHelpers.getStoreFieldsErrorsState(
                            new CreditsStoreFieldsErrorsState(),
                            error
                        );
                        this.patchState(
                            fieldsErrors,
                            'creditRefundActiveEntity',
                            'fieldsErrors'
                        );
                        reject();
                    }
                );
        });
    }

    changeCreditRefundActiveEntity(event: ChangeEvent<CreditRefund>): void {
        this.patchState(
            {...event.target, ...event.changes},
            'creditRefundActiveEntity',
            'entity'
        );
    }

    getDefaultCurrency() {
        if (
            !arrayHelpers.isEmpty(this.state.accounts) &&
            commonHelpers.isDefined(this.state.accountId)
        ) {
            return this.state.accounts.filter(account => {
                return account.id === this.state.accountId;
            })[0].currency;
        }
        return Currency.USD;
    }

    isReadOnly(credit: Credit): boolean {
        return this.authStore.hasReadOnlyAccess(
            this.state.agencyId,
            credit.accountId
        );
    }

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    private loadCredits(
        agencyId: string | null,
        accountId: string | null,
        active: boolean,
        page: number,
        pageSize: number
    ): Promise<Credit[]> {
        return new Promise<Credit[]>((resolve, reject) => {
            const offset = this.getOffset(page, pageSize);
            const serviceMethod: (
                agencyId: string | null,
                accountId: string | null,
                offset: number | null,
                limit: number | null,
                requestStateUpdater: RequestStateUpdater
            ) => Observable<Credit[]> = active
                ? this.creditsService.listActive.bind(this.creditsService)
                : this.creditsService.listPast.bind(this.creditsService);

            serviceMethod(
                agencyId,
                accountId,
                offset,
                pageSize,
                this.requestStateUpdater
            )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    (credits: Credit[]) => {
                        resolve(credits);
                    },
                    error => {
                        reject();
                    }
                );
        });
    }

    private loadTotals(
        agencyId: string,
        accountId: string
    ): Promise<CreditTotal[]> {
        return new Promise<CreditTotal[]>((resolve, reject) => {
            this.creditsService
                .totals(agencyId, accountId, this.requestStateUpdater)
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    creditTotals => {
                        resolve(creditTotals);
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

    private isSigned(credit: Credit): boolean {
        return credit.status === CreditStatus.SIGNED;
    }

    private isPaginationChanged(
        oldPagination: PaginationOptions,
        newPagination: PaginationOptions
    ): boolean {
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

    private getOffset(page: number, pageSize: number): number {
        return (page - 1) * pageSize;
    }
}
