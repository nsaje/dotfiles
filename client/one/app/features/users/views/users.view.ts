import './users.view.less';

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
import {ColDef, DetailGridInfo, GridApi} from 'ag-grid-community';
import * as moment from 'moment';
import {ActivatedRoute, ParamMap, Router} from '@angular/router';
import {UsersStore} from '../services/users-store/users.store';
import {PaginationOptions} from '../../../shared/components/smart-grid/types/pagination-options';
import {isDefined} from '../../../shared/helpers/common.helpers';
import {PaginationState} from '../../../shared/components/smart-grid/types/pagination-state';
import {
    DEFAULT_PAGINATION,
    DEFAULT_PAGINATION_OPTIONS,
    PAGINATION_URL_PARAMS,
} from '../users.config';

@Component({
    selector: 'zem-users-view',
    templateUrl: './users.view.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [UsersStore],
})
export class UsersView implements OnInit, OnDestroy {
    @HostBinding('class')
    cssClass = 'zem-users-view';

    context: any;

    keyword: string;
    paginationOptions: PaginationOptions = DEFAULT_PAGINATION_OPTIONS;

    private gridApi: GridApi;
    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(
        public store: UsersStore,
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
            .pipe(filter(queryParams => isDefined(queryParams.agencyId)))
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

    onGridReady($event: DetailGridInfo) {
        this.gridApi = $event.api;
    }

    searchUsers(keyword: string) {
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

        if (isDefined(this.gridApi)) {
            this.gridApi.showLoadingOverlay();
        }

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

    private getPreselectedPagination(): PaginationState {
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
