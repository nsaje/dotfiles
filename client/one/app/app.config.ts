import {environment} from '../environments/environment';
import {Currency, ConversionWindow} from './app.constants';
import {ConversionWindowConfig} from './core/conversion-pixels/types/conversion-windows-config';

export const CONVERSION_WINDOWS: ConversionWindowConfig[] = [
    {name: '1 day', value: ConversionWindow.LEQ_1_DAY},
    {name: '7 days', value: ConversionWindow.LEQ_7_DAYS},
    {name: '30 days', value: ConversionWindow.LEQ_30_DAYS},
];

export const APP_CONFIG = {
    env: environment.env,
    buildNumber: environment.buildNumber,
    branchName: environment.branchName,
    sentryToken: environment.sentryToken,
    staticUrl: environment.staticUrl,
    apiLegacyUrl: '/api',
    apiRestUrl: '/rest',
    apiRestInternalUrl: '/rest/internal',
    maxQueryParamsLength: 1900,
    GAKey: 'UA-74379813-2',
    mixpanelKey: '0ffce3e85e7532b547b9aad433bce9f7',
    currencySymbols: {
        [Currency.USD]: '$',
        [Currency.EUR]: '€',
        [Currency.GBP]: '£',
        [Currency.AUD]: 'A$',
        [Currency.SGD]: 'S$',
        [Currency.BRL]: 'R$',
        [Currency.MYR]: 'RM',
        [Currency.CHF]: 'CHF',
        [Currency.ZAR]: 'R',
        [Currency.ILS]: '₪',
        [Currency.INR]: '₹',
        [Currency.JPY]: '¥',
        [Currency.CAD]: 'C$',
        [Currency.NZD]: 'NZ$',
        [Currency.TRY]: '₺',
    },
    maxRequestRetries: 3,
    httpStatusCodesForRequestRetry: [504],
};
