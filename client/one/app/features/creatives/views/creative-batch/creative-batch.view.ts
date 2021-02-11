import './creative-batch.view.less';

import {Component, HostBinding, OnDestroy, OnInit} from '@angular/core';
import {combineLatest, Subject} from 'rxjs';
import {ActivatedRoute, Params} from '@angular/router';
import {map, takeUntil} from 'rxjs/operators';
import {ScopeParams} from '../../../../shared/types/scope-params';

@Component({
    selector: 'zem-creative-batch-view',
    templateUrl: './creative-batch.view.html',
})
export class CreativeBatchView implements OnInit, OnDestroy {
    @HostBinding('class')
    cssClass = 'zem-creative-batch-view';

    batchId: string | null = null;
    scopeParams: ScopeParams;

    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(private route: ActivatedRoute) {}

    ngOnInit() {
        combineLatest([this.route.params, this.route.queryParams])
            .pipe(takeUntil(this.ngUnsubscribe$))
            .pipe(
                map(([routeParams, queryParams]) => ({
                    ...routeParams,
                    ...queryParams,
                }))
            )
            .subscribe(params => {
                this.updateInternalState(params);
            });
    }

    ngOnDestroy() {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    private updateInternalState(params: Params) {
        this.scopeParams = {
            agencyId: params.agencyId,
            accountId: params.accountId || null,
        };
        this.batchId = params.batchId;
    }
}
