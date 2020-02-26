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

@Component({
    selector: 'zem-main-container',
    templateUrl: './main-container.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MainContainerComponent implements OnInit, OnDestroy {
    isSidebarVisible: boolean = false;
    opened: boolean = true;

    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(
        private router: Router,
        private changeDetectorRef: ChangeDetectorRef
    ) {}

    ngOnInit(): void {
        this.isSidebarVisible = SIDEBAR_ROUTER_PATH_NAMES.some(path =>
            this.router.url.includes(path)
        );
        this.router.events
            .pipe(takeUntil(this.ngUnsubscribe$))
            .pipe(filter(event => event instanceof NavigationEnd))
            .subscribe(() => {
                this.isSidebarVisible = SIDEBAR_ROUTER_PATH_NAMES.some(path =>
                    this.router.url.includes(path)
                );
                this.changeDetectorRef.markForCheck();
            });
    }

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }
}
