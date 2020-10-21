import {Currency, DefaultFractionSize} from '../../../../../../app.constants';
import {GridColumnTypes} from '../../../../analytics.constants';
import * as moment from 'moment';
import * as commonHelpers from '../../../../../../shared/helpers/common.helpers';
import * as numericHelpers from '../../../../../../shared/helpers/numeric.helpers';
import * as currencyHelpers from '../../../../../../shared/helpers/currency.helpers';
import {
    MIN_COLUMN_WIDTH,
    NUMBER_OF_PIXELS_PER_ADDITIONAL_CONTENT_IN_HEADER_COLUMN,
    NUMBER_OF_PIXELS_PER_CHARACTER_IN_HEADER_COLUMN,
} from '../grid-bridge.component.constants';

export function getApproximateGridColumnWidth(
    columnName: string,
    minGridColumnWidth: number = MIN_COLUMN_WIDTH,
    numberOfPixelsPerCharacter: number = NUMBER_OF_PIXELS_PER_CHARACTER_IN_HEADER_COLUMN,
    numberOfPixelsPerAdditionalContent: number = NUMBER_OF_PIXELS_PER_ADDITIONAL_CONTENT_IN_HEADER_COLUMN
): number {
    if (commonHelpers.isDefined(columnName)) {
        return Math.max(
            minGridColumnWidth,
            columnName.length * numberOfPixelsPerCharacter +
                numberOfPixelsPerAdditionalContent
        );
    }
    return minGridColumnWidth;
}

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
    return moment(columnValue).format('M/d/yyyy h:mm');
}

function formatGridColumnValueAsNumber(
    columnValue: number,
    fractionSize: number,
    defaultValue?: string
): any {
    if (!commonHelpers.isDefined(columnValue)) {
        return commonHelpers.getValueOrDefault(defaultValue, 'N/A');
    }
    return numericHelpers.parseDecimal(columnValue.toString(), fractionSize);
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
