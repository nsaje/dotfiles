/* globals describe, it, it, beforeEach, expect, module, inject */

describe('zemGridCellBaseField', function () {
    var scope, element;

    var template = '<zem-grid-cell-base-field data="ctrl.data" column="ctrl.col" row="ctrl.row" grid="ctrl.grid">' +
                   '</zem-grid-cell-base-field>';

    beforeEach(module('one'));

    beforeEach(inject(function ($rootScope, $compile) {
        scope = $rootScope.$new();

        scope.ctrl = {};
        scope.ctrl.col = {};
        scope.ctrl.col.data = {};
        scope.ctrl.grid = {};

        element = $compile(template)(scope);
    }));

    it('should display default column\'s value or N/A if field\'s value is not defined', function () {
        scope.ctrl.data = undefined;
        // Update row reference to trigger the watch on 'ctrl.row' in directive
        scope.ctrl.row = {};
        scope.$digest();
        expect(element.text().trim()).toEqual('N/A');

        scope.ctrl.col.data = {
            defaultValue: 'default',
        };
        scope.ctrl.row = {};
        scope.$digest();
        expect(element.text().trim()).toEqual('default');
    });

    it('should correctly display text values', function () {
        var tests = [
            {value: undefined, expectedResult: ''},
            {value: 'abcde', expectedResult: 'abcde'},
            {value: 12345, expectedResult: '12345'},
        ];

        scope.ctrl.col.data = {
            type: 'text',
        };

        tests.forEach(function (test) {
            scope.ctrl.data = {
                value: test.value,
            };
            scope.ctrl.row = {};
            scope.$digest();
            expect(element.text().trim()).toEqual(test.expectedResult);
        });
    });

    it('should correctly display percent values', function () {
        var tests = [
            {value: undefined, expectedResult: '0.00%'},
            {value: 0, expectedResult: '0.00%'},
            {value: 50, expectedResult: '50.00%'},
            {value: 123.45, expectedResult: '123.45%'},
        ];

        scope.ctrl.col.data = {
            type: 'percent',
            defaultValue: '0.00%',
        };

        tests.forEach(function (test) {
            scope.ctrl.data = {
                value: test.value,
            };
            scope.ctrl.row = {};
            scope.$digest();
            expect(element.text().trim()).toEqual(test.expectedResult);
        });
    });

    it('should correctly display seconds values', function () {
        var tests = [
            {value: undefined, expectedResult: 'N/A'},
            {value: 0, expectedResult: '0.0 s'},
            {value: 50, expectedResult: '50.0 s'},
            {value: 123.45, expectedResult: '123.5 s'},
        ];

        scope.ctrl.col.data = {
            type: 'seconds',
        };

        tests.forEach(function (test) {
            scope.ctrl.data = {
                value: test.value,
            };
            scope.ctrl.row = {};
            scope.$digest();
            expect(element.text().trim()).toEqual(test.expectedResult);
        });
    });

    it('should correctly display datetime values', function () {
        var tests = [
            {value: undefined, expectedResult: 'N/A'},
            {value: 1457086451517, expectedResult: '3/4/2016 5:14 AM'},
        ];

        scope.ctrl.col.data = {
            type: 'datetime',
        };

        tests.forEach(function (test) {
            scope.ctrl.data = {
                value: test.value,
            };
            scope.ctrl.row = {};
            scope.$digest();
            expect(element.text().trim()).toEqual(test.expectedResult);
        });
    });

    it('should correctly display number values', function () {
        var tests = [
            {value: undefined, expectedResult: 'N/A'},
            {value: 1234.5, expectedResult: '1,235'},
            {value: 1234.5, fractionSize: 2, expectedResult: '1,234.50'},
            {value: 0.10000, fractionSize: 3, expectedResult: '0.100'},
        ];

        scope.ctrl.col.data = {
            type: 'number',
        };

        tests.forEach(function (test) {
            scope.ctrl.col.data.fractionSize = test.fractionSize;
            scope.ctrl.data = {
                value: test.value,
            };
            scope.ctrl.row = {};
            scope.$digest();
            expect(element.text().trim()).toEqual(test.expectedResult);
        });
    });

    it('should correctly display currency values', function () {
        var tests = [
            {value: undefined, expectedResult: 'N/A'},
            {value: 1234.5, fractionSize: 2, expectedResult: '$1,234.50'},
            {value: 0.10000, fractionSize: 3, expectedResult: '$0.100'},
            {value: 0.10000, expectedResult: '$0.10'},
        ];

        scope.ctrl.col.data = {
            type: 'currency',
        };

        tests.forEach(function (test) {
            scope.ctrl.col.data.fractionSize = test.fractionSize;
            scope.ctrl.data = {
                value: test.value,
            };
            scope.ctrl.row = {};
            scope.$digest();
            expect(element.text().trim()).toEqual(test.expectedResult);
        });
    });
});
