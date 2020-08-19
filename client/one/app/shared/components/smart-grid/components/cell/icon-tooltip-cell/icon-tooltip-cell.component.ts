import './icon-tooltip-cell.component.less';

import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {IconTooltipRendererParams} from './types/icon-tooltip.renderer-params';
import {DEFAULT_DISPLAY_OPTIONS} from './icon-tooltip-cell.component.constants';
import {IconTooltipDisplayOptions} from './types/icon-tooltip-display-options';

@Component({
    templateUrl: './icon-tooltip-cell.component.html',
})
export class IconTooltipCellComponent<T1, T2, T3>
    implements ICellRendererAngularComp {
    displayOptions: IconTooltipDisplayOptions<T1>;

    agInit(params: IconTooltipRendererParams<T1, T2, T3>) {
        this.displayOptions = {
            ...DEFAULT_DISPLAY_OPTIONS,
            tooltip: params.value,
            ...params.columnDisplayOptions,
            ...params.getCellDisplayOptions?.(
                params.data,
                params.context?.componentParent
            ),
        };
    }

    refresh(): boolean {
        return false;
    }
}
