import {RulesService} from '../../../../core/rules/services/rules.service';
import {Injectable, OnDestroy, Inject} from '@angular/core';
import {Store} from 'rxjs-observable-store';
import {Subject} from 'rxjs';
import {RequestStateUpdater} from '../../../../shared/types/request-state-updater';
import {PaginationOptions} from '../../../../shared/components/smart-grid/types/pagination-options';
import {RuleHistory} from '../../../../core/rules/types/rule-history';
import {RulesHistoriesStoreState} from './rules-histories.state';
import * as storeHelpers from '../../../../shared/helpers/store.helpers';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import {takeUntil} from 'rxjs/operators';
import {Rule} from '../../../../core/rules/types/rule';
import {AdGroupService} from '../../../../core/entities/services/ad-group/ad-group.service';
import {AdGroup} from '../../../../core/entities/types/ad-group/ad-group';

@Injectable()
export class RulesHistoriesStore extends Store<RulesHistoriesStoreState>
    implements OnDestroy {
    private ngUnsubscribe$: Subject<void> = new Subject();
    private requestStateUpdater: RequestStateUpdater;
    private adGroupRequestStateUpdater: RequestStateUpdater;

    constructor(
        private rulesService: RulesService,
        private adGroupService: AdGroupService
    ) {
        super(new RulesHistoriesStoreState());
        this.requestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this
        );
        this.adGroupRequestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this,
            'adGroupRequests'
        );
    }

    setStore(
        agencyId: string | null,
        accountId: string | null,
        paginationOptions: PaginationOptions,
        ruleId: string | null,
        adGroupId: string | null,
        startDate: Date | null,
        endDate: Date | null
    ): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            Promise.all([
                this.loadRulesHistories(
                    agencyId,
                    accountId,
                    paginationOptions.page,
                    paginationOptions.pageSize,
                    ruleId,
                    adGroupId,
                    startDate,
                    endDate
                ),
                this.loadRule(ruleId),
                this.loadAdGroup(adGroupId),
            ])
                .then((values: [RuleHistory[], Rule, AdGroup]) => {
                    this.setState({
                        ...this.state,
                        agencyId: agencyId,
                        accountId: accountId,
                        entities: values[0],
                        rules: commonHelpers.isDefined(values[1])
                            ? [values[1]]
                            : [],
                        adGroups: commonHelpers.isDefined(values[2])
                            ? [values[2]]
                            : [],
                    });

                    resolve();
                })
                .catch(() => reject());
        });
    }

    loadEntities(
        paginationOptions: PaginationOptions,
        ruleId: string | null,
        adGroupId: string | null,
        startDate: Date | null,
        endDate: Date | null
    ): Promise<void> {
        return new Promise<void>((resolve, reject) => {
            this.loadRulesHistories(
                this.state.agencyId,
                this.state.accountId,
                paginationOptions.page,
                paginationOptions.pageSize,
                ruleId,
                adGroupId,
                startDate,
                endDate
            ).then(
                (histories: RuleHistory[]) => {
                    this.patchState(histories, 'entities');
                    resolve();
                },
                () => {
                    reject();
                }
            );
        });
    }

    searchRules(keyword: string): void {
        this.rulesService
            .list(
                this.state.agencyId,
                this.state.accountId,
                0,
                20,
                keyword,
                false,
                this.requestStateUpdater
            )
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe(rules => {
                this.patchState(rules, 'rules');
            });
    }

    searchAdGroups(keyword: string): void {
        this.adGroupService
            .list(
                this.state.agencyId,
                this.state.accountId,
                0,
                20,
                keyword,
                this.adGroupRequestStateUpdater
            )
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe(adGroups => {
                this.patchState(adGroups, 'adGroups');
            });
    }

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    private loadRule(ruleId: string): Promise<Rule> {
        if (!ruleId) {
            return Promise.resolve(null);
        }

        return new Promise<Rule>((resolve, reject) => {
            this.rulesService
                .get(ruleId, this.requestStateUpdater)
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    rule => {
                        resolve(rule);
                    },
                    () => {
                        reject();
                    }
                );
        });
    }

    private loadAdGroup(adGroupId: string): Promise<AdGroup> {
        if (!adGroupId) {
            return Promise.resolve(null);
        }

        return new Promise<AdGroup>((resolve, reject) => {
            this.adGroupService
                .get(adGroupId, this.adGroupRequestStateUpdater)
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    adGroupWithExtras => {
                        resolve(adGroupWithExtras.adGroup);
                    },
                    () => {
                        reject();
                    }
                );
        });
    }

    private loadRulesHistories(
        agencyId: string | null,
        accountId: string | null,
        page: number,
        pageSize: number,
        ruleId: string | null,
        adGroupId: string | null,
        startDate: Date | null,
        endDate: Date | null
    ): Promise<RuleHistory[]> {
        return new Promise<RuleHistory[]>((resolve, reject) => {
            const offset = this.getOffset(page, pageSize);
            this.rulesService
                .listHistories(
                    agencyId,
                    accountId,
                    offset,
                    pageSize,
                    ruleId,
                    adGroupId,
                    startDate,
                    endDate,
                    this.requestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    histories => {
                        resolve(histories);
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
