'use strict';

ddescribe('zemStateSelector', function() {
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

        element.find('.enabled a div.active-circle-icon').click();
        expect(isolate.onChange).toHaveBeenCalledWith(
            isolate.id, isolate.enabledValue, isolate.autopilotPausedValue);

        element.find('.enabled a div.pause-icon').click();
        expect(isolate.onChange).toHaveBeenCalledWith(
            isolate.id, isolate.pausedValue, isolate.autopilotPausedValue);

        isolate.value = 3;
        element.find('.enabled a div.auto-pilot-icon').click();
        expect(isolate.onChange).toHaveBeenCalledWith(
            isolate.id, isolate.value, isolate.autopilotEnabledValue);

        expect(isolate.onChange.calls.count()).toEqual(3);
    });
});
