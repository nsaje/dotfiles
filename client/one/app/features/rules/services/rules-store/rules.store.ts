import * as storeHelpers from '../../../../shared/helpers/store.helpers';
import {Injectable, OnDestroy, Inject} from '@angular/core';
import {Store} from 'rxjs-observable-store';
import {Subject} from 'rxjs';
import {RequestStateUpdater} from '../../../../shared/types/request-state-updater';
import {RulesService} from '../../../../core/rules/services/rules.service';
import {AccountService} from '../../../../core/entities/services/account/account.service';
import {RulesStoreState} from './rules.store.state';
import {takeUntil} from 'rxjs/operators';
import {Account} from '../../../../core/entities/types/account/account';
import {Rule} from '../../../../core/rules/types/rule';

@Injectable()
export class RulesStore extends Store<RulesStoreState> implements OnDestroy {
    private ngUnsubscribe$: Subject<void> = new Subject();
    private requestStateUpdater: RequestStateUpdater;
    private accountsRequestStateUpdater: RequestStateUpdater;

    constructor(
        private rulesService: RulesService,
        private accountsService: AccountService,
        @Inject('zemPermissions') private zemPermissions: any
    ) {
        super(new RulesStoreState());
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
        page: number,
        pageSize: number,
        keyword: string | null
    ): Promise<boolean> {
        return new Promise<boolean>(resolve => {
            Promise.all([
                this.loadRules(agencyId, accountId, page, pageSize, keyword),
                this.loadAccounts(agencyId),
            ])
                .then((values: [Rule[], Account[]]) => {
                    this.setState({
                        ...this.state,
                        agencyId: agencyId,
                        accountId: accountId,
                        hasAgencyScope: this.zemPermissions.hasAgencyScope(
                            agencyId
                        ),
                        entities: values[0],
                        accounts: values[1],
                    });
                    resolve(true);
                })
                .catch(() => resolve(false));
        });
    }

    loadEntities(
        page: number,
        pageSize: number,
        keyword: string
    ): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            this.loadRules(
                this.state.agencyId,
                this.state.accountId,
                page,
                pageSize,
                keyword
            ).then(
                (rules: Rule[]) => {
                    this.patchState(rules, 'entities');
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

    private loadRules(
        agencyId: string | null,
        accountId: string | null,
        page: number,
        pageSize: number,
        keyword: string | null
    ): Promise<Rule[]> {
        return new Promise<Rule[]>((resolve, reject) => {
            const offset = this.getOffset(page, pageSize);
            this.rulesService
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
                    (rules: Rule[]) => {
                        resolve(rules);
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
