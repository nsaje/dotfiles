import './no-rows-overlay.component.less';

import {Component, HostBinding} from '@angular/core';
import {ILoadingOverlayAngularComp} from 'ag-grid-angular';
import {ILoadingOverlayParams} from 'ag-grid-community';

@Component({
    selector: 'zem-no-rows-overlay',
    templateUrl: './no-rows-overlay.component.html',
})
export class NoRowsOverlayComponent implements ILoadingOverlayAngularComp {
    @HostBinding('class')
    cssClass = 'zem-no-rows-overlay';

    agInit(params: ILoadingOverlayParams): void {}
}
