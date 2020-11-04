import './currency-data-cell.component.less';

import {AfterViewInit, Component, ElementRef, ViewChild} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {
    EditableCellMode,
    EditableCellPlacement,
} from '../editable-cell/editable-cell.constants';
import {EditableCellApi} from '../editable-cell/types/editable-cell-api';
import {CurrencyDataRendererParams} from './type/currency-data.renderer-params';
import {GridRowDataStatsValue} from '../../grid-bridge/types/grid-row-data';
import * as commonHelpers from '../../../../../../shared/helpers/common.helpers';
import * as currencyHelpers from '../../../../../../shared/helpers/currency.helpers';
import {Grid} from '../../grid-bridge/types/grid';
import {GridRow} from '../../grid-bridge/types/grid-row';
import {
    AdGroupSettingsAutopilotState,
    Breakdown,
    Currency,
    Level,
} from '../../../../../../app.constants';
import {isAutopilotIconShown} from '../../grid-bridge/helpers/grid-bridge.helpers';
import {GridCellComponent} from '../grid-cell.component';
import {SMART_GRID_CENTER_COLS_VIEWPORT_SELECTOR} from '../../../../../../shared/components/smart-grid/smart-grid.component.constants';

@Component({
    templateUrl: './currency-data-cell.component.html',
})
export class CurrencyDataCellComponent extends GridCellComponent
    implements ICellRendererAngularComp, AfterViewInit {
    @ViewChild('hostElement', {static: false})
    hostElement: ElementRef;

    params: CurrencyDataRendererParams;

    grid: Grid;
    row: GridRow;
    level: Level;
    breakdown: Breakdown;
    campaignAutopilot: boolean;
    adGroupSettingsAutopilotState: AdGroupSettingsAutopilotState;

    valueFormatted: string;
    originalValue: string;
    value: string;

    currency: Currency;
    currencySymbol: string;
    editMessage: string;
    showAutopilotIcon: boolean;

    isSaveInProgress: boolean;
    isEditable: boolean;

    mode: EditableCellMode;
    EditableCellMode = EditableCellMode;
    placement: EditableCellPlacement;
    EditableCellPlacement = EditableCellPlacement;
    editableCellApi: EditableCellApi;

    hostElementOffsetHeight: string;
    gridElement: HTMLElement;

    agInit(params: CurrencyDataRendererParams): void {
        this.params = params;

        const statsValue = this.params.value as GridRowDataStatsValue;
        this.valueFormatted = this.params.valueFormatted;
        this.originalValue = statsValue.value as string;
        this.value = statsValue.value as string;
        if (!commonHelpers.isDefined(this.value)) {
            return;
        }

        this.grid = this.params.getGrid(this.params);
        this.row = this.params.data as GridRow;
        this.level = this.grid.meta.data.level;
        this.breakdown = this.grid.meta.data.breakdown;
        this.campaignAutopilot = this.grid.meta.data.campaignAutopilot;
        this.adGroupSettingsAutopilotState = this.grid.meta.data.adGroupAutopilotState;

        this.currency = this.grid.meta.data.ext.currency;
        this.currencySymbol = currencyHelpers.getCurrencySymbol(this.currency);

        // TODO (msuber): remove after migration to RTA completed
        this.showAutopilotIcon = isAutopilotIconShown(
            this.row,
            this.breakdown,
            this.campaignAutopilot,
            this.adGroupSettingsAutopilotState
        );

        this.isSaveInProgress = false;
        this.editMessage = commonHelpers.getValueOrDefault(
            statsValue?.editMessage,
            ''
        );
        this.isEditable = commonHelpers.getValueOrDefault(
            statsValue?.isEditable,
            false
        );

        this.mode = EditableCellMode.READ;
        this.placement = EditableCellPlacement.IN_LINE;
    }

    refresh(params: CurrencyDataRendererParams): boolean {
        const valueFormatted = params.valueFormatted;
        if (this.valueFormatted !== valueFormatted) {
            this.flashCell(params);
            return false;
        }
        return true;
    }

    ngAfterViewInit(): void {
        this.hostElementOffsetHeight = `${this.hostElement.nativeElement.offsetHeight}px`;
        this.gridElement = this.getElement(
            SMART_GRID_CENTER_COLS_VIEWPORT_SELECTOR
        );
    }

    onEditableCellReady($event: EditableCellApi) {
        this.editableCellApi = $event;
    }

    onModeChange($event: EditableCellMode) {
        this.mode = $event;
    }

    onPlacementChange($event: EditableCellPlacement) {
        this.placement = $event;
    }

    setValue($event: string) {
        this.value = $event;
    }

    save() {
        this.isSaveInProgress = true;
        this.params.setCurrencyData(this.value, this.params);
    }

    cancel() {
        this.value = this.originalValue;
        this.mode = EditableCellMode.READ;
    }
}
