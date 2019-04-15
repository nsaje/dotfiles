import {formatCurrency as angularFormatCurrency} from '@angular/common';
import * as commonHelpers from './common.helpers';
import {Currency} from '../../app.constants';
import {APP_CONFIG} from '../../app.config';

export function formatCurrency(
    value: string,
    fractionSize: number = 2,
    locale: string = 'en-US',
    currency: string = '',
    currencyCode: string = ''
): string {
    if (!commonHelpers.isDefined(value)) {
        return null;
    }
    if (isNaN(Number.parseFloat(value))) {
        return null;
    }
    const digitInfo = `1.${fractionSize}-${fractionSize}`;
    // https://angular.io/api/common/formatCurrency
    return angularFormatCurrency(
        Number.parseFloat(value),
        locale,
        currency,
        currencyCode,
        digitInfo
    );
}

export function getCurrencySymbol(currency: string): string {
    if (!commonHelpers.isDefined(currency)) {
        return APP_CONFIG.currencySymbols[Currency.USD];
    }
    return APP_CONFIG.currencySymbols[currency];
}
