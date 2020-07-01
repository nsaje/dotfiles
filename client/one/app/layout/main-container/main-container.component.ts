import './main-container.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    OnInit,
    ChangeDetectorRef,
    OnDestroy,
} from '@angular/core';
import {SIDEBAR_ROUTER_PATH_NAMES} from './main-container.component.config';
import {Router, NavigationEnd, PRIMARY_OUTLET} from '@angular/router';
import {takeUntil, filter} from 'rxjs/operators';
import {Subject} from 'rxjs';
import {RoutePathName} from '../../app.constants';
import * as commonHelpers from '../../shared/helpers/common.helpers';
import * as arrayHelpers from '../../shared/helpers/array.helpers';

@Component({
    selector: 'zem-main-container',
    templateUrl: './main-container.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MainContainerComponent implements OnInit, OnDestroy {
    routePathNames: RoutePathName[];
    isSidebarVisible: boolean = false;
    opened: boolean = true;

    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(
        private router: Router,
        private changeDetectorRef: ChangeDetectorRef
    ) {}

    ngOnInit(): void {
        this.routePathNames = this.getRoutePathNames(
            this.router,
            SIDEBAR_ROUTER_PATH_NAMES
        );
        this.isSidebarVisible = commonHelpers.isDefined(this.routePathNames);
        this.router.events
            .pipe(takeUntil(this.ngUnsubscribe$))
            .pipe(filter(event => event instanceof NavigationEnd))
            .subscribe(() => {
                this.routePathNames = this.getRoutePathNames(
                    this.router,
                    SIDEBAR_ROUTER_PATH_NAMES
                );
                this.isSidebarVisible = commonHelpers.isDefined(
                    this.routePathNames
                );
                this.changeDetectorRef.markForCheck();
            });
    }

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    private getRoutePathNames(
        router: Router,
        pathNames: RoutePathName[][]
    ): RoutePathName[] {
        const currentPath = router
            .parseUrl(router.url)
            .root.children[PRIMARY_OUTLET].segments.map(
                segment => segment.path
            );
        return (this.routePathNames = pathNames.find(path =>
            arrayHelpers.isEqual(currentPath, path)
        ));
    }
}
