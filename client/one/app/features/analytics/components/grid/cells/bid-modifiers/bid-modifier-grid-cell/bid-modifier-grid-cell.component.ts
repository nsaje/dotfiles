import {AfterViewInit, Component, Inject} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {BidModifier} from '../../../../../../../core/bid-modifiers/types/bid-modifier';
import {
    AdGroupAutopilotState,
    AdGroupSettingsAutopilotState,
    BiddingType,
    Breakdown,
    Currency,
    Level,
    SettingsState,
} from '../../../../../../../app.constants';
import {BidModifierTypeSummary} from '../../../../../../../core/bid-modifiers/types/bid-modifier-type-summary';
import {Grid} from '../../../grid-bridge/types/grid';
import {BidModifierRendererParams} from './type/bid-modifier.renderer-params';
import {GridRowDataStatsValue} from '../../../grid-bridge/types/grid-row-data';
import * as commonHelpers from '../../../../../../../shared/helpers/common.helpers';
import {GridRow} from '../../../grid-bridge/types/grid-row';
import {AUTOPILOT_BREAKDOWNS} from './bid-modifier-grid-cell.component.config';
import {DOCUMENT} from '@angular/common';
import {SMART_GRID_CENTER_COLS_VIEWPORT_SELECTOR} from '../../../../../../../shared/components/smart-grid/smart-grid.component.constants';
import {AuthStore} from '../../../../../../../core/auth/services/auth.store';

@Component({
    templateUrl: './bid-modifier-grid-cell.component.html',
})
export class BidModifierGridCellComponent
    implements ICellRendererAngularComp, AfterViewInit {
    params: BidModifierRendererParams;

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

    containerElement: HTMLElement;

    constructor(
        private authStore: AuthStore,
        @Inject(DOCUMENT) private document: Document,
        @Inject('zemNavigationNewService') private zemNavigationNewService: any
    ) {}

    agInit(params: BidModifierRendererParams): void {
        this.params = params;

        const grid: Grid = this.params.getGrid(this.params);
        const statsValue = this.params.valueFormatted as GridRowDataStatsValue;

        this.row = this.params.data as GridRow;
        this.level = grid.meta.data.level;
        this.breakdown = grid.meta.data.breakdown;
        this.campaignAutopilot = grid.meta.data.campaignAutopilot;
        this.adGroupSettingsAutopilotState =
            grid.meta.data.adGroupAutopilotState;

        this.bidModifier = commonHelpers.getValueOrDefault(
            statsValue?.value as BidModifier,
            null
        );
        this.biddingType = grid.meta.data.ext.biddingType;
        this.bid = grid.meta.data.ext.bid;
        this.bidModifierTypeSummaries = grid.meta.data.ext.typeSummaries;
        this.entityId = grid.meta.data.id;
        this.currency = grid.meta.data.ext.currency;
        this.editMessage = commonHelpers.getValueOrDefault(
            statsValue?.editMessage,
            ''
        );
        this.adGroupAutopilotState = grid.meta.data.ext.autopilotState;
        this.agencyUsesRealtimeAutopilot =
            grid.meta.data.ext.agencyUsesRealtimeAutopilot;
        this.showAutopilotIcon = this.isAutopilotIconShown(
            this.row,
            this.breakdown,
            this.campaignAutopilot,
            this.adGroupSettingsAutopilotState
        );

        this.isEditable =
            commonHelpers.getValueOrDefault(statsValue?.isEditable, false) &&
            !this.hasReadOnlyAccess(this.level);
    }

    refresh(params: BidModifierRendererParams): boolean {
        if (!commonHelpers.isDefined(this.bidModifier)) {
            return false;
        }
        const statsValue = params.valueFormatted as GridRowDataStatsValue;
        if (!commonHelpers.isDefined(statsValue)) {
            return false;
        }
        if (
            this.bidModifier.modifier !==
            (statsValue.value as BidModifier).modifier
        ) {
            return false;
        }
        return true;
    }

    ngAfterViewInit(): void {
        setTimeout(() => {
            this.containerElement = this.getContainerElement();
        });
    }

    setBidModifier($event: BidModifier) {
        this.params.setBidModifier($event, this.params);
    }

    private getContainerElement(): HTMLElement {
        const containerElements = this.document.querySelectorAll(
            SMART_GRID_CENTER_COLS_VIEWPORT_SELECTOR
        );
        return Array.from(containerElements).find(element => {
            const domRect: DOMRect = element.getBoundingClientRect();
            return domRect.width > 0 && domRect.height > 0;
        }) as HTMLElement;
    }

    private hasReadOnlyAccess(level: Level): boolean {
        if (level === Level.ALL_ACCOUNTS) {
            return true;
        }
        const account = this.zemNavigationNewService.getActiveAccount();
        return this.authStore.hasReadOnlyAccessOn(
            account.data.agencyId,
            account.id
        );
    }

    //
    // AUTOPILOT RELATED LOGIC
    // TODO (msuber): update/remove when ready
    //

    private isAutopilotIconShown(
        row: GridRow,
        breakdown: Breakdown,
        campaignAutopilot: boolean,
        adGroupSettingsAutopilotState: AdGroupSettingsAutopilotState
    ): boolean {
        if (!AUTOPILOT_BREAKDOWNS.includes(breakdown)) {
            return false;
        }
        const isRowActive: boolean = this.isRowActive(row);
        if (commonHelpers.getValueOrDefault(campaignAutopilot, false)) {
            return isRowActive;
        }
        if (
            adGroupSettingsAutopilotState ===
            AdGroupSettingsAutopilotState.INACTIVE
        ) {
            return false;
        }
        return isRowActive;
    }

    private isRowActive(row: GridRow): boolean {
        if (commonHelpers.getValueOrDefault(row.data?.archived, false)) {
            return false;
        }

        const state: GridRowDataStatsValue = row.data.stats.state;
        if (!commonHelpers.isDefined(state)) {
            return false;
        }

        return state.value === SettingsState.ACTIVE;
    }
}
