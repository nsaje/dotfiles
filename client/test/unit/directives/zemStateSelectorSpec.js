'use strict';

describe('zemStateSelector', function() {
    var $scope, element, isolate;
    var data = [];

    var template = '<zem-state-selector></zem-state-selector>';

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(inject(function($compile, $rootScope) {
        $scope = $rootScope.$new();
        element = $compile(template)($scope);

        $scope.$digest();
        isolate = element.isolateScope();
    }));

    it('calls onChange when state is changed', function() {
        isolate.id = 123;
        isolate.isEditable = true;
        isolate.autopilotShown = true;
        isolate.enabledValue = 1;
        isolate.pausedValue = 2;
        isolate.autopilotEnabledValue = 1;
        isolate.autopilotPausedValue = 2;
        isolate.onChange = function() {};

        $scope.$digest();

        spyOn(isolate, 'onChange');

        isolate.value = 1;
        isolate.autopilotValue = 1;
        element.find('.enabled a div.auto-pilot-icon').click();
        expect(isolate.onChange).not.toHaveBeenCalled();

        isolate.value = 2;
        isolate.autopilotValue = 2;
        element.find('.enabled a div.pause-icon').click();
        expect(isolate.onChange).not.toHaveBeenCalled();

        isolate.value = 1;
        isolate.autopilotValue = 2;
        element.find('.enabled a div.active-circle-icon').click();
        expect(isolate.onChange).not.toHaveBeenCalled();

        isolate.value = 1;
        isolate.autopilotValue = 1;
        element.find('.enabled a div.active-circle-icon').click();
        expect(isolate.onChange).toHaveBeenCalledWith(
            isolate.id, undefined, isolate.autopilotPausedValue);

        isolate.value = 1;
        isolate.autopilotValue = 1;
        element.find('.enabled a div.pause-icon').click();
        expect(isolate.onChange).toHaveBeenCalledWith(
            isolate.id, isolate.pausedValue, isolate.autopilotPausedValue);

        isolate.value = 2;
        isolate.autopilotValue = 2;
        element.find('.enabled a div.active-circle-icon').click();
        expect(isolate.onChange).toHaveBeenCalledWith(
            isolate.id, isolate.enabledValue, undefined);

        isolate.value = 1;
        isolate.autopilotValue = 2;
        element.find('.enabled a div.pause-icon').click();
        expect(isolate.onChange).toHaveBeenCalledWith(
            isolate.id, isolate.pausedValue, undefined);

        isolate.value = 1;
        isolate.active = true;
        isolate.autopilotValue = 2;
        element.find('.enabled a div.auto-pilot-icon').click();
        expect(isolate.onChange).toHaveBeenCalledWith(
            isolate.id, undefined, isolate.autopilotEnabledValue);

        expect(isolate.onChange.calls.count()).toEqual(5);
    });
});
