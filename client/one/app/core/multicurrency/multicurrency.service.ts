import {Injectable, Inject} from '@angular/core';
import {downgradeInjectable} from '@angular/upgrade/static';

declare var constants: any;

@Injectable()
export class MulticurrencyService {
    constructor (@Inject('zemPermissions') private zemPermissions: any) {}

    getValueInAppropriateCurrency (
        value: any,
        account: any,
        permissions: Array<string> = [],
        fractionSize?: number
    ): string {
        const currency = this.getAppropriateCurrency(account, permissions);
        return this.getValueInCurrency(value, currency, fractionSize);
    }

    getAppropriateCurrencySymbol (account: any, permissions: Array<string> = []): string {
        const currency = this.getAppropriateCurrency(account, permissions);
        return constants.currencySymbol[currency];
    }

    private getAppropriateCurrency (account: any, permissions: Array<string> = []): string {
        // TODO (jurebajt): Remove permission check after multicurrency is released (refactor tests too!)
        if (account && this.zemPermissions.hasPermission(permissions)) {
            return account.data.currency;
        }
        return constants.currency.USD;
    }

    private getValueInCurrency (value: any, currency: string, fractionSize: number = 2): string {
        const currencySymbol: string = constants.currencySymbol[currency];

        value = parseFloat(value);
        if (!isNaN(value)) {
            value = value.toFixed(fractionSize);
            return `${currencySymbol}${this.getValueWithCommas(value)}`;
        }

        return `${currencySymbol}--`;
    }

    private getValueWithCommas (value: number) {
        const parts = value.toString().split('.');
        parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        return parts.join('.');
    }
}

declare var angular: angular.IAngularStatic;
angular.module('one.downgraded').factory(
    'zemMulticurrencyService',
    downgradeInjectable(MulticurrencyService)
);
