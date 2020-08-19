import './campaign-budgets-grid.component.less';
import {Input, Component, ChangeDetectionStrategy} from '@angular/core';
import {ColDef, DetailGridInfo, GridApi} from 'ag-grid-community';
import {getValueInCurrency} from '../../../../shared/helpers/currency.helpers';
import {CampaignBudget} from '../../../../core/entities/types/campaign/campaign-budget';
import {Currency} from '../../../../app.constants';
import {IconTooltipCellComponent} from '../../../../shared/components/smart-grid/components/cell/icon-tooltip-cell/icon-tooltip-cell.component';
import {IconTooltipRendererParams} from '../../../../shared/components/smart-grid/components/cell/icon-tooltip-cell/types/icon-tooltip.renderer-params';
import {IconTooltipCellIcon} from '../../../../shared/components/smart-grid/components/cell/icon-tooltip-cell/icon-tooltip-cell.component.constants';
import * as moment from '../../../../../../lib/components/moment/moment';

@Component({
    selector: 'zem-campaign-budgets-grid',
    templateUrl: './campaign-budgets-grid.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CampaignBudgetsGridComponent {
    @Input()
    campaignBudgets: CampaignBudget[];
    @Input()
    currency: Currency;
    @Input()
    context: any;
    @Input()
    isLoading: boolean;

    columnDefs: ColDef[] = [
        {
            headerName: 'Campaign',
            field: 'campaignName',
            maxWidth: 170,
            minWidth: 100,
            resizable: false,
            cellClass: 'zem-campaign-budgets-grid__cell--wrap',
        },
        {
            headerName: 'Total Budget',
            field: 'allocatedAmount',
            maxWidth: 85,
            minWidth: 85,
            resizable: false,
            valueFormatter: params => {
                return getValueInCurrency(params.value, this.currency);
            },
        },
        {
            headerName: 'Total Spend',
            field: 'spend',
            maxWidth: 80,
            minWidth: 80,
            resizable: false,
            valueFormatter: params => {
                return getValueInCurrency(params.value, this.currency);
            },
        },
        {
            headerName: 'Flight dates',
            maxWidth: 165,
            minWidth: 100,
            resizable: false,
            valueGetter: params => {
                return `${moment(params.data.startDate).format(
                    'MM/DD/YYYY'
                )} - ${moment(params.data.endDate).format('MM/DD/YYYY')}`;
            },
            cellClass: 'zem-campaign-budgets-grid__cell--wrap',
        },
        {
            headerName: 'Notes',
            field: 'comment',
            maxWidth: 50,
            minWidth: 50,
            resizable: false,
            cellRendererFramework: IconTooltipCellComponent,
            cellRendererParams: {
                columnDisplayOptions: {
                    icon: IconTooltipCellIcon.Comment,
                },
            } as IconTooltipRendererParams<string, CampaignBudget, any>,
        },
    ];

    private gridApi: GridApi;

    onGridReady($event: DetailGridInfo) {
        this.gridApi = $event.api;
        if (this.isLoading) {
            this.gridApi.showLoadingOverlay();
        }
    }
}
