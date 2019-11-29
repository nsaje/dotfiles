import './help-popover-header.component.less';

import {Component, Input, ChangeDetectionStrategy} from '@angular/core';
import {IHeaderParams} from 'ag-grid-community';
import {IHeaderAngularComp} from 'ag-grid-angular';

@Component({
    selector: 'zem-help-popover-header',
    templateUrl: './help-popover-header.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class HelpPopoverHeaderComponent implements IHeaderAngularComp {
    params: IHeaderParams = null;

    agInit(params: IHeaderParams): void {
        this.params = params;
    }
}
