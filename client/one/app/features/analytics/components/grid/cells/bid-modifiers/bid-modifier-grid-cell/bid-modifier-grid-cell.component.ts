import {AfterViewInit, Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {BidModifier} from '../../../../../../../core/bid-modifiers/types/bid-modifier';
import {
    AdGroupAutopilotState,
    AdGroupSettingsAutopilotState,
    BiddingType,
    Breakdown,
    Currency,
    Level,
} from '../../../../../../../app.constants';
import {BidModifierTypeSummary} from '../../../../../../../core/bid-modifiers/types/bid-modifier-type-summary';
import {Grid} from '../../../grid-bridge/types/grid';
import {BidModifierRendererParams} from './types/bid-modifier.renderer-params';
import {GridRowDataStatsValue} from '../../../grid-bridge/types/grid-row-data';
import * as commonHelpers from '../../../../../../../shared/helpers/common.helpers';
import {GridRow} from '../../../grid-bridge/types/grid-row';
import {SMART_GRID_CENTER_COLS_VIEWPORT_SELECTOR} from '../../../../../../../shared/components/smart-grid/smart-grid.component.constants';
import {isAutopilotIconShown} from '../../../grid-bridge/helpers/grid-bridge.helpers';
import {GridCellComponent} from '../../grid-cell.component';

@Component({
    templateUrl: './bid-modifier-grid-cell.component.html',
})
export class BidModifierGridCellComponent extends GridCellComponent
    implements ICellRendererAngularComp, AfterViewInit {
    params: BidModifierRendererParams;

    grid: Grid;
    row: GridRow;
    level: Level;
    breakdown: Breakdown;
    campaignAutopilot: boolean;
    adGroupSettingsAutopilotState: AdGroupSettingsAutopilotState;

    bidModifier: BidModifier;
    biddingType: BiddingType;
    bid: string;
    bidModifierTypeSummaries: BidModifierTypeSummary[];
    entityId: number;
    currency: Currency;
    editMessage: string;
    adGroupAutopilotState: AdGroupAutopilotState;
    agencyUsesRealtimeAutopilot: boolean;
    showAutopilotIcon: boolean;

    isEditable: boolean;

    gridElement: HTMLElement;

    agInit(params: BidModifierRendererParams): void {
        this.params = params;

        const statsValue = this.params.value as GridRowDataStatsValue;
        this.bidModifier = commonHelpers.getValueOrDefault(
            statsValue?.value as BidModifier,
            null
        );
        if (!commonHelpers.isDefined(this.bidModifier)) {
            return;
        }

        this.grid = this.params.getGrid(this.params);
        this.row = this.params.data as GridRow;
        this.level = this.grid.meta.data.level;
        this.breakdown = this.grid.meta.data.breakdown;
        this.campaignAutopilot = this.grid.meta.data.campaignAutopilot;
        this.adGroupSettingsAutopilotState = this.grid.meta.data.adGroupAutopilotState;

        this.biddingType = this.grid.meta.data.ext.biddingType;
        this.bid = this.grid.meta.data.ext.bid;
        this.bidModifierTypeSummaries = this.grid.meta.data.ext.typeSummaries;
        this.entityId = this.grid.meta.data.id;
        this.currency = this.grid.meta.data.ext.currency;
        this.editMessage = commonHelpers.getValueOrDefault(
            statsValue?.editMessage,
            ''
        );
        this.adGroupAutopilotState = this.grid.meta.data.ext.autopilotState;
        this.agencyUsesRealtimeAutopilot = this.grid.meta.data.ext.agencyUsesRealtimeAutopilot;

        this.isEditable = commonHelpers.getValueOrDefault(
            statsValue?.isEditable,
            false
        );

        // TODO (msuber): remove after migration to RTA completed
        this.showAutopilotIcon =
            !this.isEditable &&
            isAutopilotIconShown(
                this.row,
                this.breakdown,
                this.campaignAutopilot,
                this.adGroupSettingsAutopilotState
            );
    }

    refresh(params: BidModifierRendererParams): boolean {
        const statsValue = params.value as GridRowDataStatsValue;
        if (!commonHelpers.isDefined(statsValue)) {
            return false;
        }
        if (
            this.bidModifier.modifier !==
            (statsValue.value as BidModifier).modifier
        ) {
            this.flashCell(params);
            return false;
        }
        return true;
    }

    ngAfterViewInit(): void {
        this.gridElement = this.getElement(
            SMART_GRID_CENTER_COLS_VIEWPORT_SELECTOR
        );
    }

    setBidModifier($event: BidModifier) {
        this.params.setBidModifier($event, this.params);
    }
}
