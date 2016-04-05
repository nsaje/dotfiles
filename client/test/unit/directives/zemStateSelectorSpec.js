'use strict';

describe('zemStateSelector', function () {
    var $scope, element, isolate;
    var data = [];

    var template = '<zem-state-selector></zem-state-selector>';

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(inject(function ($compile, $rootScope) {
        $scope = $rootScope.$new();
        element = $compile(template)($scope);

        $scope.$digest();
        isolate = element.isolateScope();
    }));

    it('calls onChange when state is changed', function () {
        isolate.id = 123;
        isolate.isEditable = true;
        isolate.enabledValue = 1;
        isolate.pausedValue = 2;
        isolate.onChange = function () {};

        $scope.$digest();

        spyOn(isolate, 'onChange');

        var testValues = [
            [2, 2, '.enabled a div.pause-icon'],
            [1, 2, '.enabled a div.active-circle-icon'],
            [2, 2, '.enabled a div.active-circle-icon', isolate.enabledValue],
            [1, 2, '.enabled a div.pause-icon', isolate.pausedValue]
        ];

        testValues.forEach(function (testRow) {
            isolate.value = testRow[0];
            element.find(testRow[2]).click();
            if (3 < testRow.length) {
                expect(isolate.onChange).toHaveBeenCalledWith(
                    isolate.id, testRow[3]);
            } else {
                expect(isolate.onChange).not.toHaveBeenCalled();
            }
        });

        expect(isolate.onChange.calls.count()).toEqual(4);
    });
});
