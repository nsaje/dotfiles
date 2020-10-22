import './performance-indicator-cell.component.less';

import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {PerformanceIndicatorRendererParams} from './types/performance-indicator.renderer-params';
import {Emoticon} from '../../../../../../app.constants';
import {GridRowDataStatsValue} from '../../grid-bridge/types/grid-row-data';
import * as commonHelpers from '../../../../../../shared/helpers/common.helpers';
import * as arrayHelpers from '../../../../../../shared/helpers/array.helpers';
import {EMOTICON_TO_ICON} from './performance-indicator-cell.config';
import {APP_CONFIG} from '../../../../../../app.config';
import {PerformanceIndicator} from './types/performance-indicator';

@Component({
    templateUrl: './performance-indicator-cell.component.html',
})
export class PerformanceIndicatorCellComponent
    implements ICellRendererAngularComp {
    params: PerformanceIndicatorRendererParams;

    overall: Emoticon;
    overallIconUrl: string;
    performanceIndicators: PerformanceIndicator[] = [];

    agInit(params: PerformanceIndicatorRendererParams): void {
        this.params = params;
        this.overall = this.params.valueFormatted;
        this.overallIconUrl = this.getIconUrl(this.overall);

        const value: GridRowDataStatsValue = this.params.value;
        if (
            commonHelpers.isDefined(value) &&
            !arrayHelpers.isEmpty(value.list)
        ) {
            this.performanceIndicators = value.list.map(item => {
                return {
                    ...item,
                    iconUrl: this.getIconUrl(item.emoticon || Emoticon.NEUTRAL),
                };
            });
        }
    }

    refresh(params: PerformanceIndicatorRendererParams): boolean {
        if (this.overall !== params.valueFormatted) {
            return false;
        }
        return true;
    }

    private getIconUrl(emoticon: Emoticon): string {
        return `${APP_CONFIG.staticUrl}/one/images/${EMOTICON_TO_ICON[emoticon]}`;
    }
}
