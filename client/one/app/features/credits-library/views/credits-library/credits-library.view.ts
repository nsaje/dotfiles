import './credits-library.view.less';

import {
    Component,
    ChangeDetectionStrategy,
    OnInit,
    HostBinding,
    ChangeDetectorRef,
    OnDestroy,
} from '@angular/core';
import {ActivatedRoute} from '@angular/router';
import {Subject} from 'rxjs';
import {takeUntil, filter} from 'rxjs/operators';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';

@Component({
    selector: 'zem-credits-library-view',
    templateUrl: './credits-library.view.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CreditsLibraryView implements OnInit, OnDestroy {
    @HostBinding('class')
    cssClass = 'zem-credits-library-view';

    agencyId: string;
    accountId: string;
    isInitialized: boolean = false;

    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(
        private route: ActivatedRoute,
        private changeDetectorRef: ChangeDetectorRef
    ) {}

    ngOnInit(): void {
        this.route.queryParams
            .pipe(takeUntil(this.ngUnsubscribe$))
            .pipe(
                filter(queryParams =>
                    commonHelpers.isDefined(queryParams.agencyId)
                )
            )
            .subscribe(queryParams => {
                this.agencyId = queryParams.agencyId;
                this.accountId = queryParams.accountId;
                this.isInitialized =
                    commonHelpers.isDefined(this.agencyId) ||
                    commonHelpers.isDefined(this.accountId);
                this.changeDetectorRef.markForCheck();
            });
    }

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }
}
