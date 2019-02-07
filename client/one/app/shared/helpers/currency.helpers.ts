import {formatCurrency as angularFormatCurrency} from '@angular/common';
import * as commonHelpers from './common.helpers';

export function formatCurrency(
    value: string,
    fractionSize: number = 2,
    locale: string = 'en-US',
    currency: string = '',
    currencyCode: string = ''
): string {
    if (!commonHelpers.isDefined(value)) {
        return value;
    }
    if (isNaN(Number.parseFloat(value))) {
        return;
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