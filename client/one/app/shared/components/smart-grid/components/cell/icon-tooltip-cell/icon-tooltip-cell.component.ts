import './icon-tooltip-cell.component.less';

import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import * as commonHelpers from '../../../../../helpers/common.helpers';
import {IconTooltipRendererParams} from './types/icon-tooltip.renderer-params';
import {IconTooltipCellIcon} from './icon-tooltip-cell.component.constants';

@Component({
    templateUrl: './icon-tooltip-cell.component.html',
})
export class IconTooltipCellComponent implements ICellRendererAngularComp {
    tooltip: string;
    icon: IconTooltipCellIcon;
    placement: string;

    agInit(params: IconTooltipRendererParams) {
        this.tooltip = params.value;
        this.icon = params.icon;
        this.placement = commonHelpers.getValueOrDefault(
            params.placement,
            'top'
        );
    }

    refresh(): boolean {
        return false;
    }
}
