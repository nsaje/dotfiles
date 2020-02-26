import './app-root.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    HostBinding,
    Inject,
    OnInit,
    ChangeDetectorRef,
    OnDestroy,
} from '@angular/core';
import {Router, NavigationEnd} from '@angular/router';
import {filter, takeUntil} from 'rxjs/operators';
import {Subject} from 'rxjs';
import {GoogleAnalyticsService} from './core/google-analytics/google-analytics.service';
import {MixpanelService} from './core/mixpanel/mixpanel.service';

@Component({
    selector: 'zem-app-root',
    templateUrl: './app-root.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AppRootComponent implements OnInit, OnDestroy {
    @HostBinding('class')
    cssClass = 'zem-app-root';

    isInitialized: boolean = false;
    isRendered: boolean = false;

    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(
        private router: Router,
        private changeDetectorRef: ChangeDetectorRef,
        private googleAnalyticsService: GoogleAnalyticsService,
        private mixpanelService: MixpanelService,
        @Inject('zemInitializationService')
        private zemInitializationService: any
    ) {}

    ngOnInit(): void {
        this.zemInitializationService.initApp().then(() => {
            this.googleAnalyticsService.init();
            this.mixpanelService.init();
            this.isInitialized = true;
            this.changeDetectorRef.markForCheck();
        });

        this.router.events
            .pipe(takeUntil(this.ngUnsubscribe$))
            .pipe(filter(event => event instanceof NavigationEnd))
            .subscribe(() => {
                setTimeout(() => {
                    this.isRendered = true;
                    this.changeDetectorRef.markForCheck();
                }, 250);
                this.ngUnsubscribe$.next();
                this.ngUnsubscribe$.complete();
            });
    }

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }
}
