import {Injectable} from '@angular/core';
import {BidModifierTypesGridStoreState} from './bid-modifier-types-grid.store.state';
import {Store} from 'rxjs-observable-store';
import {SmartGridColDef} from '../../../../shared/components/smart-grid/types/smart-grid-col-def';
import {GridOptions} from 'ag-grid-community';
import {TypeSummaryGridRow} from './type-summary-grid-row';
import * as numericHelpers from '../../../helpers/numeric.helpers';
import {HeaderParams} from '../../smart-grid/components/cells/header-cell/types/header-params';

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
        const columnDefs: SmartGridColDef[] = [
            {
                headerName: 'Dimension',
                field: 'type',
            },
            {
                headerName: 'Min / Max',
                field: 'limits',
                headerComponentParams: {
                    popoverTooltip:
                        'Highest (Max) and lowest (Min) bid modifiers configured per dimension.',
                    popoverPlacement: 'bottom',
                } as HeaderParams,
                valueFormatter: data => this.formatMinMaxLimits(data.value),
            },
        ];

        if (showCountColumn) {
            columnDefs.splice(1, 0, {
                headerName: '#',
                field: 'count',
                headerComponentParams: {
                    popoverTooltip:
                        'Number of configured bid modifiers per dimension.',
                    popoverPlacement: 'bottom',
                } as HeaderParams,
            });
        }

        if (selectableRows) {
            let columnDef = null;

            if (selectionTooltip) {
                columnDef = {
                    headerName: '',
                    checkboxSelection: true,
                    headerComponentParams: {
                        popoverTooltip: selectionTooltip,
                        popoverPlacement: 'bottom',
                    } as HeaderParams,
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
