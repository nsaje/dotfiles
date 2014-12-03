'use strict'

describe('decimalCurrency', function () {
    var filter;

    beforeEach(module('one'));

    beforeEach(inject(function (decimalCurrencyFilter) {
        filter = decimalCurrencyFilter;
    }));

    it('should prepend the number with a currency sign', function () {
        expect(filter('12.34', '$', 2)).toEqual('$12.34');
    });

    it('should append two decimal places by default', function () {
        expect(filter('12.34567', '$')).toEqual('$12.35');
    });

    it('should append specified number of decimal places', function () {
        expect(filter('12.34567', '$', 3)).toEqual('$12.346');
    });

    it('should delimit every three digits with a comma', function () {
        expect(filter('1234567.12345', '$', 4)).toEqual('$1,234,567.1235');
    });

    it('should return undefined in case of non-number', function () {
        expect(filter('abcd', '$', 2)).toBe(undefined);
    });
});
