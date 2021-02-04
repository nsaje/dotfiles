import './creatives.view.less';

import {Component, HostBinding, OnDestroy, OnInit} from '@angular/core';
import {ActivatedRoute, Router} from '@angular/router';
import {filter, takeUntil} from 'rxjs/operators';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import {Subject} from 'rxjs';
import {PaginationState} from '../../../../shared/components/smart-grid/types/pagination-state';
import {PAGINATION_URL_PARAMS} from '../../creatives.config';
import {AdType} from '../../../../app.constants';
import {CreativesSearchParams} from '../../creatives-shared/types/creatives-search-params';
import {ScopeParams} from '../../../../shared/types/scope-params';
import {DEFAULT_PAGINATION} from '../../creatives-shared/creatives-shared.config';
import {isNotEmpty} from '../../../../shared/helpers/common.helpers';

@Component({
    selector: 'zem-creatives-view',
    templateUrl: './creatives.view.html',
})
export class CreativesView implements OnInit, OnDestroy {
    @HostBinding('class')
    cssClass = 'zem-creatives-view';

    scopeParams: ScopeParams;
    searchParams: CreativesSearchParams;
    paginationState: PaginationState = DEFAULT_PAGINATION;

    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(private route: ActivatedRoute, private router: Router) {}

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
        this.paginationState = $event;
        this.updateUrl();
    }

    onSearchParamsChange($event: CreativesSearchParams) {
        this.searchParams = $event;
        this.updateUrl();
    }

    private updateInternalState(queryParams: any) {
        this.scopeParams = {
            agencyId: queryParams.agencyId,
            accountId: queryParams.accountId || null,
        };
        this.searchParams = {
            keyword: queryParams.keyword || null,
            creativeType: queryParams.creativeType
                ? <AdType>(<unknown>AdType[queryParams.creativeType])
                : null,
            tags: queryParams.tags ? queryParams.tags.split(',') : null,
        };
        this.paginationState = this.getPreselectedPagination();
    }

    private updateUrl() {
        const urlSearchParams = {
            keyword: this.searchParams.keyword,
            creativeType: AdType[this.searchParams.creativeType],
            tags: isNotEmpty(this.searchParams.tags)
                ? this.searchParams.tags.join(',')
                : null,
        };
        const queryParams = {
            ...this.paginationState,
            ...this.scopeParams,
            ...urlSearchParams,
        };
        this.router.navigate([], {
            relativeTo: this.route,
            queryParams,
            queryParamsHandling: 'merge',
            replaceUrl: true,
        });
    }

    private getPreselectedPagination(): PaginationState {
        const pagination = {...DEFAULT_PAGINATION};
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
