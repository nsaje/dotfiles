import {Injectable} from '@angular/core';
import {downgradeInjectable} from '@angular/upgrade/static';
import {CURRENCY, CURRENCY_SYMBOL} from '../../app.constants';

@Injectable()
export class MulticurrencyService {
    getValueInAppropriateCurrency(
        value: any,
        account: any,
        fractionSize?: number
    ): string {
        const currency = this.getAppropriateCurrency(account);
        return this.getValueInCurrency(value, currency, fractionSize);
    }

    getAppropriateCurrencySymbol(account: any): string {
        const currency = this.getAppropriateCurrency(account);
        return CURRENCY_SYMBOL[currency];
    }

    getAppropriateCurrency(account: any): string {
        if (account && account.data) {
            return account.data.currency;
        }
        return CURRENCY.USD;
    }

    private getValueInCurrency(
        value: any,
        currency: string,
        fractionSize: number = 2
    ): string {
        const currencySymbol: string = CURRENCY_SYMBOL[currency];

        value = parseFloat(value);
        if (!isNaN(value)) {
            value = value.toFixed(fractionSize);
            return `${currencySymbol}${this.getValueWithCommas(value)}`;
        }

        return `${currencySymbol}--`;
    }

    private getValueWithCommas(value: number) {
        const parts = value.toString().split('.');
        parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        return parts.join('.');
    }
}

declare var angular: angular.IAngularStatic;
angular
    .module('one.downgraded')
    .factory(
        'zemMulticurrencyService',
        downgradeInjectable(MulticurrencyService)
    );
