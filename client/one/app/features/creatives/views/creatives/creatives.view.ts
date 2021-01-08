import './creatives.view.less';

import {Component, ChangeDetectionStrategy, HostBinding} from '@angular/core';

@Component({
    selector: 'zem-creatives-view',
    templateUrl: './creatives.view.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CreativesView {
    @HostBinding('class')
    cssClass = 'zem-creatives-view';
}
