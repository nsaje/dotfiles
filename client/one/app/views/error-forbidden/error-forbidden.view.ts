import './error-forbidden.view.less';

import {Component, ChangeDetectionStrategy, HostBinding} from '@angular/core';
import {downgradeComponent} from '@angular/upgrade/static';

@Component({
    selector: 'zem-error-forbidden-view',
    templateUrl: './error-forbidden.view.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ErrorForbiddenView {
    @HostBinding('class')
    cssClass = 'zem-error-forbidden-view';
}

declare var angular: angular.IAngularStatic;
angular.module('one.downgraded').directive(
    'zemErrorForbiddenView',
    downgradeComponent({
        component: ErrorForbiddenView,
        propagateDigest: false,
    })
);
