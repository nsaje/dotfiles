import './help-popover-header.component.less';

import {Component, ChangeDetectionStrategy} from '@angular/core';
import {IHeaderAngularComp} from 'ag-grid-angular';
import {HelpPopoverHeaderParams} from './types/help-popover-header-params';

@Component({
    selector: 'zem-help-popover-header',
    templateUrl: './help-popover-header.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class HelpPopoverHeaderComponent implements IHeaderAngularComp {
    params: HelpPopoverHeaderParams = null;

    agInit(params: HelpPopoverHeaderParams): void {
        this.params = params;
    }
}
