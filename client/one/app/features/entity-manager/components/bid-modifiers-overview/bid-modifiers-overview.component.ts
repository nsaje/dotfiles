import './bid-modifiers-overview.component.less';

import {APP_CONFIG} from '../../../../app.config';
import {BID_MODIFIER_TYPE_NAME_MAP} from '../../../../core/bid-modifiers/bid-modifiers.config';
import {
    Component,
    ChangeDetectionStrategy,
    EventEmitter,
    Input,
    Output,
    OnChanges,
} from '@angular/core';
import {ColDef, GridOptions} from 'ag-grid-community';
import {BidModifierTypeSummary} from '../../../../core/bid-modifiers/types/bid-modifier-type-summary';
import {HelpPopoverHeaderComponent} from '../../../../shared/components/smart-grid/components/header/help-popover/help-popover-header.component';
import {BidModifiersImportErrorState} from '../../services/ad-group-settings-store/bid-modifiers-import-error-state';
import {BidModifierUploadSummary} from 'one/app/core/bid-modifiers/types/bid-modifier-upload-summary';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import * as numericHelpers from '../../../../shared/helpers/numeric.helpers';

@Component({
    selector: 'zem-bid-modifiers-overview',
    templateUrl: './bid-modifiers-overview.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BidModifiersOverviewComponent implements OnChanges {
    @Input()
    adGroupId: String;
    @Input()
    bidModifierTypeSummaries: BidModifierTypeSummary[];
    @Input()
    importError: BidModifiersImportErrorState;
    @Input()
    importSummary: BidModifierUploadSummary;
    @Output()
    importFileChange = new EventEmitter<File>();

    showOnlyNonGlobal: boolean = true;

    gridOptions: GridOptions = {
        suppressMovableColumns: true,
    };

    columnDefs: ColDef[] = [
        {
            headerName: 'Dimension',
            field: 'type',
            valueFormatter: data => BID_MODIFIER_TYPE_NAME_MAP[data.value],
        },
        {
            headerName: '#',
            field: 'count',
            headerComponentParams: {
                tooltip: 'Number of configured bid modifiers per dimension.',
                popoverPlacement: 'bottom',
            },
            headerComponentFramework: HelpPopoverHeaderComponent,
        },
        {
            headerName: 'Min / Max',
            field: 'limits',
            headerComponentParams: {
                tooltip:
                    'Highest (Max) and lowest (Min) bid modifiers configured per dimension.',
                popoverPlacement: 'bottom',
            },
            headerComponentFramework: HelpPopoverHeaderComponent,
            valueFormatter: data => this.formatMinMaxLimits(data.value),
        },
    ];

    gridRowData: any = null;

    ngOnChanges(): void {
        this.gridRowData = this.getGridRowData();
    }

    private getGridRowData(): any {
        if (!commonHelpers.isDefined(this.bidModifierTypeSummaries)) {
            return null;
        }

        return this.bidModifierTypeSummaries.map(item => {
            return {
                type: item.type,
                count: item.count,
                limits: {
                    min: item.min,
                    max: item.max,
                },
            };
        });
    }

    private formatMinMaxLimits(limits: any): string {
        return (
            numericHelpers.convertNumberToPercentValue(
                limits.min - 1.0,
                true,
                0
            ) +
            ' / ' +
            numericHelpers.convertNumberToPercentValue(
                limits.max - 1.0,
                true,
                0
            )
        );
    }

    exportBidModifiers(): void {
        if (!commonHelpers.isDefined(this.adGroupId)) {
            return;
        }
        const url = `${APP_CONFIG.apiRestInternalUrl}/adgroups/${
            this.adGroupId
        }/bidmodifiers/download/`;
        window.open(url, '_blank');
    }

    downloadCsvSampleFile(): void {
        if (!commonHelpers.isDefined(this.adGroupId)) {
            return;
        }
        const url = `${
            APP_CONFIG.apiRestInternalUrl
        }/adgroups/bidmodifiers/example_csv_download/`;
        window.open(url, '_blank');
    }

    downloadErrorsFile(): void {
        if (!commonHelpers.isDefined(this.importError)) {
            return;
        }
        const url = commonHelpers.isDefined(this.adGroupId)
            ? `${APP_CONFIG.apiRestInternalUrl}/adgroups/${
                  this.adGroupId
              }/bidmodifiers/error_download/${this.importError.errorFileUrl}/`
            : `${
                  APP_CONFIG.apiRestInternalUrl
              }/adgroups/bidmodifiers/error_download/${
                  this.importError.errorFileUrl
              }/`;
        window.open(url, '_blank');
    }

    onFilesChange($event: File[]): void {
        const file: File = $event.length > 0 ? $event[0] : null;
        this.importFileChange.emit(file);
    }
}
