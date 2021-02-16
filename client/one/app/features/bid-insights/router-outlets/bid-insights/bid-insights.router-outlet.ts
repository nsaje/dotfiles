import {Component, OnInit, OnDestroy, ChangeDetectorRef} from '@angular/core';
import {ActivatedRoute, Router} from '@angular/router';
import {Subject} from 'rxjs';
import {takeUntil} from 'rxjs/operators';
import {BID_INSIGHTS_CONFIG} from '../../bid-insights.config';

@Component({
    selector: 'zem-bid-insights-router-outlet',
    templateUrl: './bid-insights.router-outlet.html',
})
// tslint:disable-next-line component-class-suffix
export class BidInsightsRouterOutlet implements OnInit, OnDestroy {
    adGroupId: string;

    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(
        private router: Router,
        private outletRoute: ActivatedRoute,
        private changeDetectorRef: ChangeDetectorRef
    ) {}

    ngOnInit() {
        this.outletRoute.queryParams
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe(queryParams => {
                this.adGroupId = queryParams[BID_INSIGHTS_CONFIG.idQueryParam];
                this.changeDetectorRef.markForCheck();
            });
    }

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }
}
