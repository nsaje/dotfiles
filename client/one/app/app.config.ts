import {environment} from '../environments/environment';
import {Currency, ConversionWindow} from './app.constants';
import {CurrencyConfig} from './types/currency-config';

export const CONVERSION_WINDOW_NUMBER_FORMAT = {
    [ConversionWindow.LEQ_1_DAY]: 24,
    [ConversionWindow.LEQ_7_DAYS]: 168,
    [ConversionWindow.LEQ_30_DAYS]: 720,
    [ConversionWindow.LEQ_90_DAYS]: 2160,
};

export const APP_CONFIG = {
    env: environment.env,
    buildNumber: environment.buildNumber,
    branchName: environment.branchName,
    sentryToken: environment.sentryToken,
    staticUrl: environment.staticUrl,
    workerUrl: environment.workerUrl,
    apiLegacyUrl: '/api',
    apiRestUrl: '/rest',
    apiRestInternalUrl: '/rest/internal',
    maxQueryParamsLength: 1900,
    GAKey: 'UA-74379813-2',
    mixpanelKey: '0ffce3e85e7532b547b9aad433bce9f7',
    posthogKey: 'LyK-gxP1FXkWDECkmKgbbHsMPDdov-ayiP3OqxN259U',
    posthogApiHost: 'https://app.posthog.com',
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
        [Currency.MXN]: 'Mex$',
    },
    requestRetryTimeout: 500,
    maxRequestRetries: 3,
    httpStatusCodesForRequestRetry: [504],
    httpErrorPopupIncludeHttpMethods: ['PUT', 'POST', 'DELETE'],
    httpErrorPopupExcludeUrlRegexes: [/.*(\/breakdown\/).*/],
};

export const CURRENCIES: CurrencyConfig[] = [
    {name: 'US Dollar', value: Currency.USD},
    {name: 'Euro', value: Currency.EUR},
    {name: 'British Pound', value: Currency.GBP},
    {name: 'Australian Dollar', value: Currency.AUD},
    {name: 'Singapore Dollar', value: Currency.SGD},
    {name: 'Brazilian Real', value: Currency.BRL},
    {name: 'Malaysian Ringgit', value: Currency.MYR},
    {name: 'Swiss Franc', value: Currency.CHF},
    {name: 'South African Rand', value: Currency.ZAR},
    {name: 'Israeli New Shekel', value: Currency.ILS},
    {name: 'Indian Rupee', value: Currency.INR},
    {name: 'Japanese Yen', value: Currency.JPY},
    {name: 'Canadian Dollar', value: Currency.CAD},
    {name: 'New Zealand Dollar', value: Currency.NZD},
    {name: 'Turkish Lira', value: Currency.TRY},
    {name: 'Mexican Peso', value: Currency.MXN},
];
