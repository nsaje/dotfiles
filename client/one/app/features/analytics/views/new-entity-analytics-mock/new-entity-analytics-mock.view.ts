import './new-entity-analytics-mock.view.less';

import {Component, ChangeDetectionStrategy, HostBinding} from '@angular/core';
import {downgradeComponent} from '@angular/upgrade/static';

@Component({
    selector: 'zem-new-entity-analytics-mock-view',
    templateUrl: './new-entity-analytics-mock.view.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NewEntityAnalyticsMockView {
    @HostBinding('class')
    cssClass = 'zem-new-entity-analytics-mock-view';
}

declare var angular: angular.IAngularStatic;
angular.module('one.downgraded').directive(
    'zemNewEntityAnalyticsMockView',
    downgradeComponent({
        component: NewEntityAnalyticsMockView,
        propagateDigest: false,
    })
);
