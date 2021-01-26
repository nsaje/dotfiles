import {Component, HostBinding} from '@angular/core';
import {ILoadingOverlayAngularComp} from 'ag-grid-angular';
import {ILoadingOverlayParams} from 'ag-grid-community';

@Component({
    selector: 'zem-grid-loading-overlay',
    templateUrl: './grid-loading-overlay.component.html',
})
export class GridLoadingOverlayComponent implements ILoadingOverlayAngularComp {
    @HostBinding('class')
    cssClass = 'zem-grid-loading-overlay';

    agInit(params: ILoadingOverlayParams): void {}
}
