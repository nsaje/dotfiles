import './main-container.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    OnInit,
    Inject,
    ChangeDetectorRef,
} from '@angular/core';
import {downgradeComponent} from '@angular/upgrade/static';
import {SIDEBAR_UI_ROUTER_STATE_NAMES} from './main-container.component.config';

@Component({
    selector: 'zem-main-container',
    templateUrl: './main-container.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MainContainerComponent implements OnInit {
    isSidebarVisible: boolean = false;
    opened: boolean = true;

    constructor(
        private changeDetectorRef: ChangeDetectorRef,
        @Inject('ajs$rootScope') private ajs$rootScope: any,
        @Inject('ajs$state') private ajs$state: any
    ) {}

    ngOnInit(): void {
        this.isSidebarVisible = SIDEBAR_UI_ROUTER_STATE_NAMES.includes(
            this.ajs$state.$current.name
        );
        this.ajs$rootScope.$on('$zemStateChangeSuccess', () => {
            this.isSidebarVisible = SIDEBAR_UI_ROUTER_STATE_NAMES.includes(
                this.ajs$state.$current.name
            );
            this.changeDetectorRef.markForCheck();
        });
    }
}

declare var angular: angular.IAngularStatic;
angular.module('one.downgraded').directive(
    'zemMainContainer',
    downgradeComponent({
        component: MainContainerComponent,
        propagateDigest: false,
    })
);
