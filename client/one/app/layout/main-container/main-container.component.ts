import './main-container.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    OnInit,
    ChangeDetectorRef,
    OnDestroy,
} from '@angular/core';
import {SIDEBAR_ROUTER_PATH_NAMES} from './main-container.component.config';
import {Router, NavigationEnd} from '@angular/router';
import {takeUntil, filter} from 'rxjs/operators';
import {Subject} from 'rxjs';
import {RoutePathName} from '../../app.constants';
import * as commonHelpers from '../../shared/helpers/common.helpers';

@Component({
    selector: 'zem-main-container',
    templateUrl: './main-container.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MainContainerComponent implements OnInit, OnDestroy {
    routePathName: RoutePathName;
    isSidebarVisible: boolean = false;
    opened: boolean = true;

    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(
        private router: Router,
        private changeDetectorRef: ChangeDetectorRef
    ) {}

    ngOnInit(): void {
        this.routePathName = SIDEBAR_ROUTER_PATH_NAMES.find(path =>
            this.router.url.includes(path)
        );
        this.isSidebarVisible = commonHelpers.isDefined(this.routePathName);
        this.router.events
            .pipe(takeUntil(this.ngUnsubscribe$))
            .pipe(filter(event => event instanceof NavigationEnd))
            .subscribe(() => {
                this.routePathName = SIDEBAR_ROUTER_PATH_NAMES.find(path =>
                    this.router.url.includes(path)
                );
                this.isSidebarVisible = commonHelpers.isDefined(
                    this.routePathName
                );
                this.changeDetectorRef.markForCheck();
            });
    }

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }
}
