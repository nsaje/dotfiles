import './new-entity-analytics-mock.view.less';

import {Component, ChangeDetectionStrategy, HostBinding} from '@angular/core';

@Component({
    selector: 'zem-new-entity-analytics-mock-view',
    templateUrl: './new-entity-analytics-mock.view.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NewEntityAnalyticsMockView {
    @HostBinding('class')
    cssClass = 'zem-new-entity-analytics-mock-view';
}
