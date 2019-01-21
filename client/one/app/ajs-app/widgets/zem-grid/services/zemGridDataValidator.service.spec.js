describe('zemGridDataValidator', function() {
    var zemGridDataValidator, tests, options;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function(_zemGridDataValidator_) {
        zemGridDataValidator = _zemGridDataValidator_;
    }));

    it('should correctly validate currency values', function() {
        tests = [
            {value: '1234', fractionSize: 2, expectedResult: true},
            {value: '12.34', fractionSize: 2, expectedResult: true},
            {value: '0.1', fractionSize: 2, expectedResult: true},
            {value: '00.12', fractionSize: 2, expectedResult: true},
            {value: '0.', fractionSize: 2, expectedResult: true},
            {value: '.1', fractionSize: 2, expectedResult: true},
            {value: undefined, expectedResult: false},
            {value: ' ', fractionSize: 2, expectedResult: false},
            {value: 'a', fractionSize: 2, expectedResult: false},
            {value: '1a', fractionSize: 2, expectedResult: false},
            {value: '1..', fractionSize: 2, expectedResult: false},
            {value: '1.a', fractionSize: 2, expectedResult: false},
            {value: '1,', fractionSize: 2, expectedResult: false},
            {value: '0.123', fractionSize: 2, expectedResult: false},
            {value: '0.123', expectedResult: false},
            {value: '0.123', fractionSize: 3, expectedResult: true},
            {value: '0.', fractionSize: 0, expectedResult: false},
        ];

        tests.forEach(function(test) {
            options = {
                type: 'currency',
                fractionSize: test.fractionSize,
            };
            expect(zemGridDataValidator.validate(test.value, options)).toBe(
                test.expectedResult
            );
        });
    });
});
