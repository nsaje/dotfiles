import './loading-overlay.component.less';

import {Component, HostBinding} from '@angular/core';
import {ILoadingOverlayAngularComp} from 'ag-grid-angular';
import {ILoadingOverlayParams} from 'ag-grid-community';

@Component({
    selector: 'zem-loading-overlay',
    templateUrl: './loading-overlay.component.html',
})
export class LoadingOverlayComponent implements ILoadingOverlayAngularComp {
    @HostBinding('class')
    cssClass = 'zem-loading-overlay';

    agInit(params: ILoadingOverlayParams): void {}
}
