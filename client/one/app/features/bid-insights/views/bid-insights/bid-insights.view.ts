import './bid-insights.view.less';

import {
    Component,
    ChangeDetectionStrategy,
    HostBinding,
    Input,
    AfterViewInit,
} from '@angular/core';
import {ActivatedRoute, Router} from '@angular/router';
import {ChangeDetectorRef} from '@angular/core';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import * as arrayHelpers from '../../../../shared/helpers/array.helpers';
import {BID_INSIGHTS_CONFIG} from '../../bid-insights.config';

@Component({
    selector: 'zem-bid-insights',
    templateUrl: './bid-insights.view.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [],
})
export class BidInsightsView implements AfterViewInit {
    @HostBinding('class')
    cssClass = 'zem-bid-insights-view';

    @Input()
    adGroupId: string;

    isOpen: boolean;

    context: any;
    constructor(
        private route: ActivatedRoute,
        private router: Router,
        private changeDetectorRef: ChangeDetectorRef
    ) {
        this.context = {
            componentParent: this,
        };
    }

    ngAfterViewInit() {
        setTimeout(() => {
            this.open();
        }, 1000);
    }

    open() {
        this.isOpen = true;
        this.changeDetectorRef.detectChanges();
    }

    close() {
        this.isOpen = false;
        this.navigateToRoute([]);
    }

    private navigateToRoute(routePath: string[]) {
        this.isOpen = false;
        this.router
            .navigate(
                [
                    {
                        outlets: {drawer: null},
                    },
                ],
                {
                    queryParams: commonHelpers.getValueWithoutProps(
                        this.router.routerState.root.snapshot.queryParams,
                        [BID_INSIGHTS_CONFIG.idQueryParam]
                    ),
                }
            )
            .then(() => {
                if (!arrayHelpers.isEmpty(routePath)) {
                    this.router.navigate(routePath, {
                        queryParamsHandling: 'preserve',
                    });
                }
            });
    }
}
