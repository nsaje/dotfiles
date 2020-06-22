import {RulesService} from '../../../../core/rules/services/rules.service';
import {Injectable, OnDestroy, Inject} from '@angular/core';
import {Store} from 'rxjs-observable-store';
import {Subject} from 'rxjs';
import {RequestStateUpdater} from '../../../../shared/types/request-state-updater';
import {PaginationOptions} from '../../../../shared/components/smart-grid/types/pagination-options';
import {RuleHistory} from '../../../../core/rules/types/rule-history';
import {RulesHistoriesStoreState} from './rules-histories.state';
import * as storeHelpers from '../../../../shared/helpers/store.helpers';
import {takeUntil} from 'rxjs/operators';

@Injectable()
export class RulesHistoriesStore extends Store<RulesHistoriesStoreState>
    implements OnDestroy {
    private ngUnsubscribe$: Subject<void> = new Subject();
    private requestStateUpdater: RequestStateUpdater;

    constructor(private rulesService: RulesService) {
        super(new RulesHistoriesStoreState());
        this.requestStateUpdater = storeHelpers.getStoreRequestStateUpdater(
            this
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
            this.loadRulesHistories(
                agencyId,
                accountId,
                paginationOptions.page,
                paginationOptions.pageSize,
                ruleId,
                adGroupId,
                startDate,
                endDate
            )
                .then((histories: RuleHistory[]) => {
                    this.setState({
                        ...this.state,
                        agencyId: agencyId,
                        accountId: accountId,
                        entities: histories,
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

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
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
