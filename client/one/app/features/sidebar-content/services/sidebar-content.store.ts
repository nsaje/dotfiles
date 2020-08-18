import {Injectable, OnDestroy, Inject} from '@angular/core';
import {Store} from 'rxjs-observable-store';
import {SidebarContentStoreState} from './sidebar-content.store.state';
import {Subject} from 'rxjs';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import * as storeHelpers from '../../../shared/helpers/store.helpers';
import * as commonHelpers from '../../../shared/helpers/common.helpers';
import * as arrayHelpers from '../../../shared/helpers/array.helpers';
import {Agency} from '../../../core/entities/types/agency/agency';
import {Account} from '../../../core/entities/types/account/account';
import {AgencyService} from '../../../core/entities/services/agency/agency.service';
import {AccountService} from '../../../core/entities/services/account/account.service';
import {takeUntil} from 'rxjs/operators';
import {AuthStore} from '../../../core/auth/services/auth.store';

@Injectable()
export class SidebarContentStore extends Store<SidebarContentStoreState>
    implements OnDestroy {
    private ngUnsubscribe$: Subject<undefined> = new Subject();
    private agenciesRequestStateUpdater: RequestStateUpdater;
    private accountsRequestStateUpdater: RequestStateUpdater;

    constructor(
        private agencyService: AgencyService,
        private accountService: AccountService,
        private authStore: AuthStore
    ) {
        super(new SidebarContentStoreState());

        this.agenciesRequestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this,
            'agenciesRequests'
        );
        this.accountsRequestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this,
            'accountsRequests'
        );
    }

    setStore(agencyId: string | null, accountId: string | null) {
        if (arrayHelpers.isEmpty(this.state.agencies)) {
            this.initStore(agencyId, accountId);
        } else {
            agencyId = agencyId || this.state.agencies[0].id;
            this.loadAccounts(agencyId).then((accounts: Account[]) => {
                this.setState({
                    ...this.state,
                    accounts: accounts,
                    selectedAgencyId: agencyId,
                    selectedAccountId: this.getSelectedAccountId(
                        agencyId,
                        accountId,
                        accounts
                    ),
                });
            });
        }
    }

    setSelectedAgency(agencyId: string) {
        this.loadAccounts(agencyId).then((accounts: Account[]) => {
            this.setState({
                ...this.state,
                selectedAgencyId: agencyId,
                accounts: accounts,
                selectedAccountId: this.getSelectedAccountId(
                    agencyId,
                    null,
                    accounts
                ),
            });
        });
    }

    setSelectedAccount(accountId: string) {
        this.patchState(accountId, 'selectedAccountId');
    }

    private initStore(agencyId: string | null, accountId: string | null) {
        this.loadAgencies().then((agencies: Agency[]) => {
            if (
                !commonHelpers.isDefined(agencyId) &&
                !arrayHelpers.isEmpty(agencies)
            ) {
                agencyId = agencies[0].id;
            }
            this.loadAccounts(agencyId).then((accounts: Account[]) => {
                this.setState({
                    ...this.state,
                    agencies: agencies,
                    accounts: accounts,
                    selectedAgencyId: agencyId,
                    selectedAccountId: this.getSelectedAccountId(
                        agencyId,
                        accountId,
                        accounts
                    ),
                });
            });
        });
    }

    private getSelectedAccountId(
        agencyId: string,
        accountId: string | null,
        accounts: Account[] | null
    ): string | null {
        if (commonHelpers.isDefined(accountId)) {
            return accountId;
        } else if (
            this.authStore.hasAgencyScope(agencyId) ||
            arrayHelpers.isEmpty(accounts)
        ) {
            return null;
        } else {
            return accounts[0].id;
        }
    }

    private loadAgencies(): Promise<Agency[]> {
        return new Promise<Agency[]>((resolve, reject) => {
            this.agencyService
                .list(this.agenciesRequestStateUpdater)
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    (agencies: Agency[]) => {
                        resolve(agencies);
                    },
                    error => {
                        reject();
                    }
                );
        });
    }

    private loadAccounts(agencyId: string | null): Promise<Account[]> {
        return new Promise<Account[]>((resolve, reject) => {
            this.accountService
                .list(
                    agencyId,
                    null,
                    null,
                    null,
                    this.accountsRequestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    (accounts: Account[]) => {
                        resolve(accounts);
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
}
