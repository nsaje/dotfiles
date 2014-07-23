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

    it('should return null in case of non-number', function () {
        expect(filter('abcd', '$', 2)).toBe(undefined);
    });
});
