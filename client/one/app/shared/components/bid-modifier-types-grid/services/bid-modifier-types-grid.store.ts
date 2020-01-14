import {Injectable} from '@angular/core';
import {BidModifierTypesGridStoreState} from './bid-modifier-types-grid.store.state';
import {Store} from 'rxjs-observable-store';
import {ColDef, GridOptions} from 'ag-grid-community';
import {HelpPopoverHeaderComponent} from '../../smart-grid/components/header/help-popover/help-popover-header.component';
import {TypeSummaryGridRow} from './type-summary-grid-row';
import * as numericHelpers from '../../../helpers/numeric.helpers';

@Injectable()
export class BidModifierTypesGridStore extends Store<
    BidModifierTypesGridStoreState
> {
    constructor() {
        super(new BidModifierTypesGridStoreState());
    }

    updateGridConfig(
        showCountColumn: boolean,
        selectableRows: boolean,
        selectionTooltip: string
    ): void {
        const gridOptions: GridOptions = {
            suppressMovableColumns: true,
        };
        const columnDefs: ColDef[] = [
            {
                headerName: 'Dimension',
                field: 'type',
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

        if (showCountColumn) {
            columnDefs.splice(1, 0, {
                headerName: '#',
                field: 'count',
                headerComponentParams: {
                    tooltip:
                        'Number of configured bid modifiers per dimension.',
                    popoverPlacement: 'bottom',
                },
                headerComponentFramework: HelpPopoverHeaderComponent,
            });
        }

        if (selectableRows) {
            let columnDef = null;

            if (selectionTooltip) {
                columnDef = {
                    headerName: '',
                    checkboxSelection: true,
                    headerComponentParams: {
                        tooltip: selectionTooltip,
                        popoverPlacement: 'bottom',
                    },
                    headerComponentFramework: HelpPopoverHeaderComponent,
                    minWidth: 40,
                    maxWidth: 40,
                };
            } else {
                columnDef = {
                    headerName: '',
                    checkboxSelection: true,
                };
            }

            columnDefs.splice(0, 0, columnDef);
        }

        this.setState({
            ...this.state,
            showCountColumn: showCountColumn,
            selectableRows: selectableRows,
            selectionTooltip: selectionTooltip,
            gridOptions: gridOptions,
            columnDefs: columnDefs,
        });
    }

    updateTypeSummaryGridRows(typeSummaryGridRows: TypeSummaryGridRow[]): void {
        if (
            JSON.stringify(typeSummaryGridRows) ===
            JSON.stringify(this.state.typeSummaryGridRows)
        ) {
            return;
        }

        this.setState({
            ...this.state,
            typeSummaryGridRows: typeSummaryGridRows,
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
}
