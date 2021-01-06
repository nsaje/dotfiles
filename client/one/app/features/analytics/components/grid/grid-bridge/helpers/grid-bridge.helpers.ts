import {
    AdGroupSettingsAutopilotState,
    Breakdown,
    Currency,
    DefaultFractionSize,
    SettingsState,
} from '../../../../../../app.constants';
import {GridColumnTypes} from '../../../../analytics.constants';
import * as moment from 'moment';
import * as commonHelpers from '../../../../../../shared/helpers/common.helpers';
import * as numericHelpers from '../../../../../../shared/helpers/numeric.helpers';
import * as currencyHelpers from '../../../../../../shared/helpers/currency.helpers';
import * as arrayHelpers from '../../../../../../shared/helpers/array.helpers';
import {GridRow} from '../types/grid-row';
import {GridRowDataStatsValue} from '../types/grid-row-data';
import {AUTOPILOT_BREAKDOWNS} from '../grid-bridge.component.config';
import {SmartGridColDef} from '../../../../../../shared/components/smart-grid/types/smart-grid-col-def';
export interface FormatGridColumnValueOptions {
    type: GridColumnTypes;
    fractionSize?: number;
    currency?: Currency;
    defaultValue?: string;
}

export function formatGridColumnValue(
    columnValue: number | string,
    formatterOptions: FormatGridColumnValueOptions
): string {
    switch (formatterOptions.type) {
        case GridColumnTypes.TEXT:
            return formatGridColumnValueAsText(
                columnValue as string,
                formatterOptions.defaultValue
            );
        case GridColumnTypes.PERCENT:
            return formatGridColumnValueAsPercent(
                columnValue as number,
                DefaultFractionSize.PERCENT,
                formatterOptions.defaultValue
            );
        case GridColumnTypes.SECONDS:
            return formatGridColumnValueAsSeconds(
                columnValue as number,
                DefaultFractionSize.SECONDS,
                formatterOptions.defaultValue
            );
        case GridColumnTypes.DATE_TIME:
            return formatGridColumnValueAsDateTime(
                columnValue as string,
                formatterOptions.defaultValue
            );
        case GridColumnTypes.NUMBER:
            return formatGridColumnValueAsNumber(
                columnValue as number,
                commonHelpers.getValueOrDefault(
                    formatterOptions.fractionSize,
                    DefaultFractionSize.NUMBER
                ),
                formatterOptions.defaultValue
            );
        case GridColumnTypes.CURRENCY:
            return formatGridColumnValueAsCurrency(
                columnValue as number,
                commonHelpers.getValueOrDefault(
                    formatterOptions.currency,
                    Currency.USD
                ),
                DefaultFractionSize.CURRENCY,
                formatterOptions.defaultValue
            );
        default:
            if (commonHelpers.isDefined(columnValue)) {
                return columnValue.toString();
            }
            return commonHelpers.getValueOrDefault(
                formatterOptions.defaultValue,
                'N/A'
            );
    }
}

export function getColumnsInOrder(
    columns: SmartGridColDef[],
    columnsOrder: string[]
): SmartGridColDef[] {
    if (arrayHelpers.isEmpty(columns) || arrayHelpers.isEmpty(columnsOrder)) {
        return columns;
    }

    const columnsInOrder: SmartGridColDef[] = [];

    columnsOrder.forEach(field => {
        const column: SmartGridColDef = columns.find(
            column => column.field === field
        );
        if (commonHelpers.isDefined(column)) {
            columnsInOrder.push(column);
        }
    });

    columns
        .filter(column => {
            return !columnsInOrder.includes(column);
        })
        .forEach(column => {
            const columnRightNeighbor: SmartGridColDef = getRightNeighbor(
                columns,
                columnsInOrder,
                column
            );
            commonHelpers.isDefined(columnRightNeighbor)
                ? columnsInOrder.splice(
                      columnsInOrder.indexOf(columnRightNeighbor),
                      0,
                      column
                  )
                : columnsInOrder.push(column);
        });
    return columnsInOrder;
}

function getRightNeighbor(
    columns: SmartGridColDef[],
    columnsInOrder: SmartGridColDef[],
    column: SmartGridColDef
): SmartGridColDef {
    if (arrayHelpers.isEmpty(columns) || arrayHelpers.isEmpty(columnsInOrder)) {
        return null;
    }
    if (!columns.includes(column)) {
        return null;
    }

    const columnIndex: number = columns.indexOf(column);
    if (columnIndex === columns.length - 1) {
        return null;
    }

    const columnRightNeighbor: SmartGridColDef =
        columns
            .slice(columnIndex + 1)
            .find(column => columnsInOrder.includes(column)) || null;
    return columnRightNeighbor;
}

function formatGridColumnValueAsText(
    columnValue: string,
    defaultValue?: string
): string {
    if (!commonHelpers.isDefined(columnValue)) {
        return commonHelpers.getValueOrDefault(defaultValue, '');
    }
    return columnValue;
}

function formatGridColumnValueAsPercent(
    columnValue: number,
    fractionSize: number,
    defaultValue?: string
): any {
    if (!commonHelpers.isDefined(columnValue)) {
        return commonHelpers.getValueOrDefault(defaultValue, 'N/A');
    }
    return `${numericHelpers.parseDecimal(
        columnValue.toString(),
        fractionSize
    )}%`;
}

function formatGridColumnValueAsSeconds(
    columnValue: number,
    fractionSize: number,
    defaultValue?: string
): any {
    if (!commonHelpers.isDefined(columnValue)) {
        return commonHelpers.getValueOrDefault(defaultValue, 'N/A');
    }
    return `${numericHelpers.parseDecimal(
        columnValue.toString(),
        fractionSize
    )}s`;
}

function formatGridColumnValueAsDateTime(
    columnValue: string,
    defaultValue?: string
): any {
    if (!commonHelpers.isDefined(columnValue)) {
        return commonHelpers.getValueOrDefault(defaultValue, 'N/A');
    }
    return moment(columnValue).format('M/D/YYYY h:mm A');
}

function formatGridColumnValueAsNumber(
    columnValue: number,
    fractionSize: number,
    defaultValue?: string
): any {
    if (!commonHelpers.isDefined(columnValue)) {
        return commonHelpers.getValueOrDefault(defaultValue, 'N/A');
    }
    return numericHelpers.formatNumber(columnValue, fractionSize);
}

function formatGridColumnValueAsCurrency(
    columnValue: number,
    currency: Currency,
    fractionSize: number,
    defaultValue?: string
): any {
    if (!commonHelpers.isDefined(columnValue)) {
        return commonHelpers.getValueOrDefault(defaultValue, 'N/A');
    }

    return currencyHelpers.formatCurrency(
        columnValue.toString(),
        currency,
        fractionSize
    );
}

//
// AUTOPILOT RELATED LOGIC
// TODO (msuber): remove after migration to RTA completed
//

export function isAutopilotIconShown(
    row: GridRow,
    breakdown: Breakdown,
    campaignAutopilot: boolean,
    adGroupSettingsAutopilotState: AdGroupSettingsAutopilotState
): boolean {
    if (!AUTOPILOT_BREAKDOWNS.includes(breakdown)) {
        return false;
    }
    if (commonHelpers.getValueOrDefault(campaignAutopilot, false)) {
        return isRowActive(row);
    }
    if (
        adGroupSettingsAutopilotState === AdGroupSettingsAutopilotState.INACTIVE
    ) {
        return false;
    }
    return isRowActive(row);
}

function isRowActive(row: GridRow): boolean {
    if (commonHelpers.getValueOrDefault(row.data?.archived, false)) {
        return false;
    }

    const state: GridRowDataStatsValue = row.data.stats
        .state as GridRowDataStatsValue;
    if (!commonHelpers.isDefined(state)) {
        return false;
    }

    return state.value === SettingsState.ACTIVE;
}
