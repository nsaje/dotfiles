import * as storeHelpers from '../../../../shared/helpers/store.helpers';
import {Injectable, OnDestroy} from '@angular/core';
import {Store} from 'rxjs-observable-store';
import {Subject} from 'rxjs';
import {RequestStateUpdater} from '../../../../shared/types/request-state-updater';
import {RulesService} from '../../../../core/rules/services/rules.service';
import {RulesStoreState} from './rules.store.state';
import {takeUntil} from 'rxjs/operators';
import {Rule} from '../../../../core/rules/types/rule';
import * as clone from 'clone';
import {AuthStore} from '../../../../core/auth/services/auth.store';

@Injectable()
export class RulesStore extends Store<RulesStoreState> implements OnDestroy {
    private ngUnsubscribe$: Subject<void> = new Subject();
    private requestStateUpdater: RequestStateUpdater;

    constructor(
        private rulesService: RulesService,
        private authStore: AuthStore
    ) {
        super(new RulesStoreState());
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
            this.loadRules(agencyId, accountId, page, pageSize, keyword)
                .then(rules => {
                    this.setState({
                        ...this.state,
                        agencyId: agencyId,
                        accountId: accountId,
                        hasAgencyScope: this.authStore.hasAgencyScope(agencyId),
                        entities: rules,
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

    archiveEntity(ruleId: string): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            this.rulesService
                .archive(ruleId, this.requestStateUpdater)
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    () => {
                        resolve();
                    },
                    () => {
                        reject();
                    }
                );
        });
    }

    enableRule(ruleId: string): void {
        this.rulesService
            .enable(ruleId, this.requestStateUpdater)
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe(savedChangedRule => {
                this.updateRule(savedChangedRule);
            });
    }

    pauseRule(ruleId: string): void {
        this.rulesService
            .pause(ruleId, this.requestStateUpdater)
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe(savedChangedRule => {
                this.updateRule(savedChangedRule);
            });
    }

    setActiveEntity(rule: Partial<Rule>) {
        this.setState({
            ...this.state,
            activeEntity: {
                entity: rule,
                isReadOnly: this.isReadOnly(rule),
            },
        });
    }

    isReadOnly(rule: Partial<Rule>): boolean {
        return this.authStore.hasReadOnlyAccess(
            this.state.agencyId,
            rule.accountId
        );
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

    private getOffset(page: number, pageSize: number): number {
        return (page - 1) * pageSize;
    }

    private updateRule(savedChangedRule: Rule): void {
        const rules = clone(this.state.entities);
        const index = rules.findIndex(rule => rule.id === savedChangedRule.id);
        if (index !== -1) {
            rules[index] = savedChangedRule;
            this.patchState(rules, 'entities');
        }
    }
}
