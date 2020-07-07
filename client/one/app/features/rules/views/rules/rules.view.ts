import './rules.view.less';

import {
    Component,
    ChangeDetectionStrategy,
    OnInit,
    OnDestroy,
    HostBinding,
    Inject,
} from '@angular/core';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import {Subject} from 'rxjs';
import {ActivatedRoute, Router} from '@angular/router';
import {takeUntil, filter} from 'rxjs/operators';
import {PaginationState} from '../../../../shared/components/smart-grid/types/pagination-state';
import {PaginationOptions} from '../../../../shared/components/smart-grid/types/pagination-options';
import {RulesStore} from '../../services/rules-store/rules.store';
import {
    DEFAULT_PAGINATION_OPTIONS,
    DEFAULT_PAGINATION,
    PAGINATION_URL_PARAMS,
} from '../../rules.config';

@Component({
    selector: 'zem-rules-view',
    templateUrl: './rules.view.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [RulesStore],
})
export class RulesView implements OnInit, OnDestroy {
    @HostBinding('class')
    cssClass = 'zem-rules-view';

    context: any;

    keyword: string;
    paginationOptions: PaginationOptions = DEFAULT_PAGINATION_OPTIONS;

    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(
        public store: RulesStore,
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

    ngOnDestroy() {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    onPaginationChange($event: PaginationState) {
        this.router.navigate([], {
            relativeTo: this.route,
            queryParams: $event,
            queryParamsHandling: 'merge',
            replaceUrl: true,
        });
    }

    searchRules(keyword: string) {
        this.router.navigate([], {
            relativeTo: this.route,
            queryParams: {keyword: keyword},
            queryParamsHandling: 'merge',
            replaceUrl: true,
        });
    }

    private updateInternalState(queryParams: any) {
        const agencyId = queryParams.agencyId;
        const accountId = queryParams.accountId || null;
        this.keyword = queryParams.keyword || null;
        this.paginationOptions = {
            ...this.paginationOptions,
            ...this.getPreselectedPagination(),
        };

        if (
            agencyId !== this.store.state.agencyId ||
            accountId !== this.store.state.accountId
        ) {
            this.store.setStore(
                agencyId,
                accountId,
                this.paginationOptions.page,
                this.paginationOptions.pageSize,
                this.keyword
            );
        } else {
            this.store.loadEntities(
                this.paginationOptions.page,
                this.paginationOptions.pageSize,
                this.keyword
            );
        }
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
}
