/* globals describe, it, beforeEach, expect, module, inject */

describe('test zemGridDataFormatter', function () {
    var zemGridDataFormatter,
        tests,
        options;

    beforeEach(module('one'));

    beforeEach(inject(function (_zemGridDataFormatter_) {
        zemGridDataFormatter = _zemGridDataFormatter_;
    }));

    it('should return unformatted values for unknown types', function () {
        tests = [
            {value: 'abc', expectedResult: 'abc'},
            {value: 123, expectedResult: 123},
        ];

        options = {
            type: 'unknown',
        };

        tests.forEach(function (test) {
            expect(zemGridDataFormatter.formatValue(test.value, options)).toEqual(test.expectedResult);
        });
    });

    it('should correctly format percent values', function () {
        tests = [
            {value: undefined, expectedResult: 'N/A'},
            {value: 0, expectedResult: '0.00%'},
            {value: 50, expectedResult: '50.00%'},
        ];

        options = {
            type: 'percent',
        };

        tests.forEach(function (test) {
            expect(zemGridDataFormatter.formatValue(test.value, options)).toEqual(test.expectedResult);
        });
    });

    it('should correctly format seconds values', function () {
        tests = [
            {value: undefined, expectedResult: 'N/A'},
            {value: 0, expectedResult: '0.0 s'},
            {value: 10, expectedResult: '10.0 s'},
        ];

        options = {
            type: 'seconds',
        };

        tests.forEach(function (test) {
            expect(zemGridDataFormatter.formatValue(test.value, options)).toEqual(test.expectedResult);
        });
    });

    it('should correctly format datetime values', function () {
        tests = [
            {value: undefined, expectedResult: 'N/A'},
            {value: 1457086451517, expectedResult: '3/4/2016 5:14 AM'},
        ];

        options = {
            type: 'datetime',
        };

        tests.forEach(function (test) {
            expect(zemGridDataFormatter.formatValue(test.value, options)).toEqual(test.expectedResult);
        });
    });

    it('should correctly format number values', function () {
        tests = [
            {value: undefined, expectedResult: 'N/A'},
            {value: 0, fractionSize: 4, expectedResult: '0.0000'},
            {value: 1234.56, fractionSize: 4, expectedResult: '1,234.5600'},
            {value: 1234.56, expectedResult: '1,235'},
        ];

        tests.forEach(function (test) {
            options = {
                type: 'number',
                fractionSize: test.fractionSize,
            };
            expect(zemGridDataFormatter.formatValue(test.value, options)).toEqual(test.expectedResult);
        });
    });

    it('should correctly format currency values', function () {
        tests = [
            {value: undefined, expectedResult: 'N/A'},
            {value: 0, fractionSize: 2, expectedResult: '$0.00'},
            {value: 1234.5678, expectedResult: '$1,234.57'},
            {value: 1234.56, fractionSize: 3, expectedResult: '$1,234.560'},
            {value: 1234.56, fractionSize: 0, expectedResult: '$1,235'},
        ];

        tests.forEach(function (test) {
            options = {
                type: 'currency',
                fractionSize: test.fractionSize,
            };
            expect(zemGridDataFormatter.formatValue(test.value, options)).toEqual(test.expectedResult);
        });
    });
});
