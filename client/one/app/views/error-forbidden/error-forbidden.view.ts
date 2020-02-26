import './error-forbidden.view.less';

import {Component, ChangeDetectionStrategy, HostBinding} from '@angular/core';

@Component({
    selector: 'zem-error-forbidden-view',
    templateUrl: './error-forbidden.view.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ErrorForbiddenView {
    @HostBinding('class')
    cssClass = 'zem-error-forbidden-view';
}
