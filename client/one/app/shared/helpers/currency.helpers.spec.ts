import * as currencyHelpers from './currency.helpers';

describe('CurrencyHelpers', () => {
    it('should prepend the number with a currency sign', () => {
        expect(
            currencyHelpers.formatCurrency('12.34', 2, 'en-US', '$')
        ).toEqual('$12.34');
    });

    it('should append two decimal places by default', () => {
        expect(currencyHelpers.formatCurrency('12.34567')).toEqual('12.35');
    });

    it('should append specified number of decimal places', () => {
        expect(currencyHelpers.formatCurrency('12.34567', 3)).toEqual('12.346');
    });

    it('should delimit every three digits with a comma', () => {
        expect(currencyHelpers.formatCurrency('1234567.12345', 4)).toEqual(
            '1,234,567.1235'
        );
    });

    it('should return undefined in case of non-number', () => {
        expect(currencyHelpers.formatCurrency('abcd', 2)).toBe(undefined);
    });
});