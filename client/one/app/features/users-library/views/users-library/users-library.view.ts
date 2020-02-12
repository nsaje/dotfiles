import './users-library.view.less';

import {
    Component,
    ChangeDetectionStrategy,
    OnInit,
    OnDestroy,
    Inject,
    HostBinding,
    ChangeDetectorRef,
} from '@angular/core';
import {downgradeComponent} from '@angular/upgrade/static';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';

@Component({
    selector: 'zem-users-library-view',
    templateUrl: './users-library.view.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class UsersLibraryView implements OnInit, OnDestroy {
    @HostBinding('class')
    cssClass = 'zem-users-library-view';

    account: any;

    private stateChangeListener$: Function;
    private locationChangeListener$: Function;

    constructor(
        private changeDetectorRef: ChangeDetectorRef,
        @Inject('ajs$rootScope') private ajs$rootScope: any,
        @Inject('zemNavigationNewService') private zemNavigationNewService: any
    ) {}

    ngOnInit(): void {
        this.updateInternalState();
        this.stateChangeListener$ = this.ajs$rootScope.$on(
            '$zemStateChangeSuccess',
            () => {
                this.updateInternalState();
            }
        );
        this.locationChangeListener$ = this.ajs$rootScope.$on(
            '$locationChangeSuccess',
            () => {
                this.updateInternalState();
            }
        );
    }

    ngOnDestroy(): void {
        if (commonHelpers.isDefined(this.stateChangeListener$)) {
            this.stateChangeListener$();
        }
        if (commonHelpers.isDefined(this.locationChangeListener$)) {
            this.locationChangeListener$();
        }
    }

    updateInternalState() {
        if (!commonHelpers.isDefined(this.account)) {
            this.account = this.zemNavigationNewService.getActiveAccount();
            this.changeDetectorRef.markForCheck();
        }
    }
}

declare var angular: angular.IAngularStatic;
angular.module('one.downgraded').directive(
    'zemUsersLibraryView',
    downgradeComponent({
        component: UsersLibraryView,
        propagateDigest: false,
    })
);
