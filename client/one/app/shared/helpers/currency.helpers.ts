import {formatCurrency as angularFormatCurrency} from '@angular/common';
import * as commonHelpers from './common.helpers';
import {Currency} from '../../app.constants';
import {APP_CONFIG} from '../../app.config';

export function formatCurrency(
    value: string,
    currency: Currency,
    fractionSize: number = 2
): string {
    if (!commonHelpers.isDefined(value)) {
        return null;
    }
    if (isNaN(Number.parseFloat(value))) {
        return null;
    }
    const digitInfo = `1.${fractionSize}-${fractionSize}`;
    const currencySymbol = commonHelpers.isDefined(currency)
        ? getCurrencySymbol(currency)
        : '';
    // https://angular.io/api/common/formatCurrency
    return angularFormatCurrency(
        Number.parseFloat(value),
        'en-US', // locale
        currencySymbol,
        '', // currencyCode: USD, EUR, ...
        digitInfo
    );
}

export function getCurrencySymbol(currency: Currency): string {
    if (!commonHelpers.isDefined(currency)) {
        return APP_CONFIG.currencySymbols[Currency.USD];
    }
    return APP_CONFIG.currencySymbols[currency];
}

export function getValueInCurrency(
    value: string,
    currency: Currency,
    fractionSize: number = 2
): string {
    const formattedValue = formatCurrency(value, currency, fractionSize);
    if (formattedValue) {
        return formattedValue;
    }
    const currencySymbol = commonHelpers.isDefined(currency)
        ? getCurrencySymbol(currency)
        : '';
    return `${currencySymbol}--`;
}
