describe('zemGridDataFormatter', function() {
    var zemGridDataFormatter, tests, options;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function(_zemGridDataFormatter_) {
        zemGridDataFormatter = _zemGridDataFormatter_;
    }));

    it('should return unformatted values for unknown types', function() {
        tests = [
            {value: undefined, expectedResult: 'N/A'},
            {value: 'abc', expectedResult: 'abc'},
            {value: 123, expectedResult: 123},
        ];

        options = {
            type: 'unknown',
        };

        tests.forEach(function(test) {
            expect(
                zemGridDataFormatter.formatValue(test.value, options)
            ).toEqual(test.expectedResult);
        });
    });

    it('should correctly format text values', function() {
        tests = [
            {value: undefined, expectedResult: ''},
            {value: 'abcde', expectedResult: 'abcde'},
            {value: 12345, expectedResult: '12345'},
        ];

        options = {
            type: 'text',
        };

        tests.forEach(function(test) {
            expect(
                zemGridDataFormatter.formatValue(test.value, options)
            ).toEqual(test.expectedResult);
        });
    });

    it('should correctly format percent values', function() {
        tests = [
            {value: undefined, expectedResult: 'N/A'},
            {value: 0, expectedResult: '0.00%'},
            {value: 50, expectedResult: '50.00%'},
        ];

        options = {
            type: 'percent',
        };

        tests.forEach(function(test) {
            expect(
                zemGridDataFormatter.formatValue(test.value, options)
            ).toEqual(test.expectedResult);
        });
    });

    it('should correctly format seconds values', function() {
        tests = [
            {value: undefined, expectedResult: 'N/A'},
            {value: 0, expectedResult: '0.0 s'},
            {value: 10, expectedResult: '10.0 s'},
        ];

        options = {
            type: 'seconds',
        };

        tests.forEach(function(test) {
            expect(
                zemGridDataFormatter.formatValue(test.value, options)
            ).toEqual(test.expectedResult);
        });
    });

    it('should correctly format dateTime values', function() {
        tests = [
            {value: undefined, expectedResult: 'N/A'},
            {
                value: '2016-03-04T11:14:12.123999',
                expectedResult: '3/4/2016 11:14 AM',
            },
        ];

        options = {
            type: 'dateTime',
        };

        tests.forEach(function(test) {
            expect(
                zemGridDataFormatter.formatValue(test.value, options)
            ).toEqual(test.expectedResult);
        });
    });

    it('should correctly format number values', function() {
        tests = [
            {value: undefined, expectedResult: 'N/A'},
            {value: 0, fractionSize: 4, expectedResult: '0.0000'},
            {value: 1234.56, fractionSize: 4, expectedResult: '1,234.5600'},
            {value: 1234.56, expectedResult: '1,235'},
        ];

        tests.forEach(function(test) {
            options = {
                type: 'number',
                fractionSize: test.fractionSize,
            };
            expect(
                zemGridDataFormatter.formatValue(test.value, options)
            ).toEqual(test.expectedResult);
        });
    });

    it('should correctly format currency values', function() {
        tests = [
            {value: undefined, expectedResult: 'N/A'},
            {value: 0, fractionSize: 2, expectedResult: '$0.00'},
            {value: 1234.5678, expectedResult: '$1,234.57'},
            {value: 1234.56, fractionSize: 3, expectedResult: '$1,234.560'},
            {value: 1234.56, fractionSize: 0, expectedResult: '$1,235'},
            {
                value: undefined,
                currency: constants.currency.EUR,
                expectedResult: 'N/A',
            },
            {
                value: 0,
                fractionSize: 2,
                currency: constants.currency.EUR,
                expectedResult: '€0.00',
            },
            {
                value: 1234.5678,
                currency: constants.currency.EUR,
                expectedResult: '€1,234.57',
            },
            {
                value: 1234.56,
                fractionSize: 3,
                currency: constants.currency.EUR,
                expectedResult: '€1,234.560',
            },
            {
                value: 1234.56,
                fractionSize: 0,
                currency: constants.currency.EUR,
                expectedResult: '€1,235',
            },
        ];

        tests.forEach(function(test) {
            options = {
                type: 'currency',
                fractionSize: test.fractionSize,
                currency: test.currency,
            };
            expect(
                zemGridDataFormatter.formatValue(test.value, options)
            ).toEqual(test.expectedResult);
        });
    });

    it('should correctly round number values', function() {
        tests = [
            {value: undefined, expectedResult: undefined},
            {value: 0, fractionSize: 2, expectedResult: '0.00'},
            {value: 1234.5678, expectedResult: '1235'},
            {value: 1234.56, fractionSize: 3, expectedResult: '1234.560'},
            {value: 1234.56, fractionSize: 0, expectedResult: '1235'},
        ];

        tests.forEach(function(test) {
            options = {
                type: 'number',
                fractionSize: test.fractionSize,
            };
            expect(
                zemGridDataFormatter.parseInputValue(test.value, options)
            ).toEqual(test.expectedResult);
        });
    });

    it('should correctly round currency values', function() {
        tests = [
            {value: undefined, expectedResult: undefined},
            {value: 0, fractionSize: 2, expectedResult: '0.00'},
            {value: 1234.5678, expectedResult: '1234.57'},
            {value: 1234.56, fractionSize: 3, expectedResult: '1234.560'},
            {value: 1234.56, fractionSize: 0, expectedResult: '1235'},
        ];

        tests.forEach(function(test) {
            options = {
                type: 'currency',
                fractionSize: test.fractionSize,
            };
            expect(
                zemGridDataFormatter.parseInputValue(test.value, options)
            ).toEqual(test.expectedResult);
        });
    });
});
