import './breakdown-cell.component.less';

import {Component, Inject} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {BreakdownRendererParams} from './types/breakdown.renderer-params';
import * as commonHelpers from '../../../../../../shared/helpers/common.helpers';
import {
    ENTITIES_WITH_EXTERNAL_LINKS,
    ENTITIES_WITH_INTERNAL_LINKS,
} from './breakdown-cell.component.config';
import {GridRowDataStatsValue} from '../../grid-bridge/types/grid-row-data';
import {BreakdownValueType} from './breakdown-cell.component.constants';

@Component({
    templateUrl: './breakdown-cell.component.html',
})
export class BreakdownCellComponent implements ICellRendererAngularComp {
    params: BreakdownRendererParams;
    valueFormatted: string;
    valueType: BreakdownValueType;
    url: string;
    redirectorUrl: string;
    popoverTooltip: string;

    BreakdownValueType = BreakdownValueType;

    constructor(
        @Inject('zemNavigationNewService') private zemNavigationNewService: any
    ) {}

    agInit(params: BreakdownRendererParams): void {
        this.params = params;
        this.valueFormatted = this.params.valueFormatted;
        this.popoverTooltip = this.params.getPopoverTooltip(this.params);

        this.valueType = BreakdownValueType.TEXT;
        const entity = this.params.getEntity(this.params);
        if (commonHelpers.isDefined(entity)) {
            if (ENTITIES_WITH_INTERNAL_LINKS.includes(entity.type)) {
                this.valueType = BreakdownValueType.INTERNAL_LINK;
                this.url = this.zemNavigationNewService.getEntityHref(
                    entity,
                    true
                );
            }
            if (ENTITIES_WITH_EXTERNAL_LINKS.includes(entity.type)) {
                this.valueType = BreakdownValueType.EXTERNAL_LINK;
                this.url = (this.params.value as GridRowDataStatsValue).url;
                this.redirectorUrl = (this.params
                    .value as GridRowDataStatsValue).redirectorUrl;
            }
        }
    }

    refresh(params: BreakdownRendererParams): boolean {
        if (this.valueFormatted !== params.valueFormatted) {
            return false;
        }
        return true;
    }

    openUrl($event: MouseEvent) {
        $event.preventDefault();
        if (
            this.shouldOpenInNewTab($event) ||
            this.valueType === BreakdownValueType.EXTERNAL_LINK
        ) {
            window.open(this.redirectorUrl || this.url, '_blank');
        } else {
            this.params.navigateByUrl(this.params, this.url);
        }
    }

    private shouldOpenInNewTab($event: MouseEvent): boolean {
        return $event.ctrlKey || $event.metaKey;
    }
}
