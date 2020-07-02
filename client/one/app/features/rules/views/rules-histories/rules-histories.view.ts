import './rules-histories.view.less';

import {
    Component,
    ChangeDetectionStrategy,
    OnInit,
    OnDestroy,
    HostBinding,
    Inject,
} from '@angular/core';
import {Subject} from 'rxjs';
import {takeUntil, filter} from 'rxjs/operators';
import {PaginationOptions} from '../../../../shared/components/smart-grid/types/pagination-options';
import {PaginationState} from '../../../../shared/components/smart-grid/types/pagination-state';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import {ActivatedRoute, Router} from '@angular/router';
import {RulesHistoriesStore} from '../../services/rules-histories-store/rules-histories.store';
import {
    PAGINATION_URL_PARAMS,
    DEFAULT_PAGINATION,
    DEFAULT_PAGINATION_OPTIONS,
} from '../../rules.config';
import {RuleHistory} from '../../../../core/rules/types/rule-history';
import {RuleHistoryStatus} from '../../../../core/rules/rules.constants';

@Component({
    selector: 'zem-rules-histories-view',
    templateUrl: './rules-histories.view.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [RulesHistoriesStore],
})
export class RulesHistoriesView implements OnInit, OnDestroy {
    @HostBinding('class')
    cssClass = 'zem-rules-histories-view';

    context: any;

    paginationOptions: PaginationOptions = DEFAULT_PAGINATION_OPTIONS;

    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(
        public store: RulesHistoriesStore,
        private route: ActivatedRoute,
        private router: Router,
        @Inject('zemPermissions') public zemPermissions: any
    ) {
        this.context = {
            componentParent: this,
        };
    }

    ngOnInit() {
        this.route.queryParams
            .pipe(takeUntil(this.ngUnsubscribe$))
            .pipe(
                filter(queryParams =>
                    commonHelpers.isDefined(queryParams.agencyId)
                )
            )
            .subscribe(queryParams => {
                this.updateInternalState(queryParams);
            });
    }

    onPaginationChange($event: PaginationState) {
        this.router.navigate([], {
            relativeTo: this.route,
            queryParams: $event,
            queryParamsHandling: 'merge',
            replaceUrl: true,
        });
    }

    private updateInternalState(queryParams: any) {
        const agencyId = queryParams.agencyId;
        const accountId = queryParams.accountId || null;

        this.paginationOptions = {
            ...this.paginationOptions,
            ...this.getPreselectedPagination(),
        };

        this.store.setStore(
            agencyId,
            accountId,
            this.paginationOptions,
            null,
            null,
            null,
            null
        );
    }

    private getPreselectedPagination(): {page: number; pageSize: number} {
        const pagination: PaginationState = {...DEFAULT_PAGINATION};
        PAGINATION_URL_PARAMS.forEach(paramName => {
            const value: string = this.route.snapshot.queryParamMap.get(
                paramName
            );
            if (value) {
                pagination[paramName] = Number(value);
            }
        });
        return pagination;
    }

    ngOnDestroy() {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }
}