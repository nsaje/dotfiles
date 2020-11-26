import './campaign-budgets-grid.component.less';
import {Input, Component, ChangeDetectionStrategy} from '@angular/core';
import {SmartGridColDef} from '../../../../shared/components/smart-grid/types/smart-grid-col-def';
import {DetailGridInfo, GridApi} from 'ag-grid-community';
import {getValueInCurrency} from '../../../../shared/helpers/currency.helpers';
import {CampaignBudget} from '../../../../core/entities/types/campaign/campaign-budget';
import {Currency} from '../../../../app.constants';
import {IconTooltipCellComponent} from '../../../../shared/components/smart-grid/components/cells/icon-tooltip-cell/icon-tooltip-cell.component';
import {IconTooltipRendererParams} from '../../../../shared/components/smart-grid/components/cells/icon-tooltip-cell/types/icon-tooltip.renderer-params';
import {IconTooltipCellIcon} from '../../../../shared/components/smart-grid/components/cells/icon-tooltip-cell/icon-tooltip-cell.component.constants';
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

    columnDefs: SmartGridColDef[] = [
        {
            headerName: 'Campaign',
            field: 'campaignName',
            maxWidth: 170,
            minWidth: 100,
            cellClass: 'zem-campaign-budgets-grid__cell--wrap',
        },
        {
            headerName: 'Total Budget',
            field: 'allocatedAmount',
            maxWidth: 85,
            minWidth: 85,
            valueFormatter: params => {
                return getValueInCurrency(params.value, this.currency);
            },
        },
        {
            headerName: 'Total Spend',
            field: 'spend',
            maxWidth: 80,
            minWidth: 80,
            valueFormatter: params => {
                return getValueInCurrency(params.value, this.currency);
            },
        },
        {
            headerName: 'Flight dates',
            maxWidth: 165,
            minWidth: 100,
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
