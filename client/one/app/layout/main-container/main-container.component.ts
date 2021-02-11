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
import {isDefined} from '../../shared/helpers/common.helpers';

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
        this.updateSidebar();
        this.router.events
            .pipe(takeUntil(this.ngUnsubscribe$))
            .pipe(filter(event => event instanceof NavigationEnd))
            .subscribe(() => {
                this.updateSidebar();
                this.changeDetectorRef.markForCheck();
            });
    }

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    private updateSidebar() {
        this.routePathNames = this.getCurrentRoutePathNames(
            this.router,
            SIDEBAR_ROUTER_PATH_NAMES
        );
        this.isSidebarVisible = isDefined(this.routePathNames);
    }

    private getCurrentRoutePathNames(
        router: Router,
        allPathNames: RoutePathName[][]
    ): RoutePathName[] {
        const currentPath: string[] = router
            .parseUrl(router.url)
            .root.children[PRIMARY_OUTLET].segments.map(
                segment => segment.path
            );
        return allPathNames.find(path =>
            this.urlMatchesPath(currentPath, path)
        );
    }

    private urlMatchesPath(
        urlParts: string[],
        pathParts: RoutePathName[]
    ): boolean {
        if (urlParts.length !== pathParts.length) {
            return false;
        }
        for (let index = 0; index < urlParts.length; index++) {
            const urlPart: string = urlParts[index];
            const pathPart: RoutePathName = pathParts[index];
            if (pathPart !== RoutePathName.ANY && pathPart !== urlPart) {
                return false;
            }
        }
        return true;
    }
}
