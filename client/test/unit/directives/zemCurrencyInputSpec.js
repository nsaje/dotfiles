'use strict';

describe('zemCurrencyInput', function () {
    var $scope;
    var $compile;

    var prepareElement = function () {
        var element = $compile('<input type="text" ng-model="value" zem-currency-input>')($scope);
        $scope.$digest();

        return element;
    };

    var setVal = function (element, value, triggerBlur) {
        element.val(value).trigger('input');
        if (triggerBlur) {
            element.trigger('blur');
        }
    };

    beforeEach(module('one'));
    
    // $state needs to be mocked because of
    // some strange issues with ui-router
    // https://github.com/angular-ui/ui-router/issues/212
    beforeEach(module('stateMock'));

    beforeEach(inject(function ($rootScope, _$compile_) {
        $scope = $rootScope.$new();
        $compile = _$compile_;
    }));

    it('formats input with commas on every change', function () {
        var element = prepareElement();

        setVal(element, '1234567');
        expect(element.val()).toEqual('1,234,567');
        expect($scope.value).toEqual('1234567');
    });

    it('takes only first dot into account in case there are more', function () {
        var element = prepareElement();

        setVal(element, '12.34.56');
        expect(element.val()).toEqual('12.34');
        expect($scope.value).toEqual('12.34');

        setVal(element, '12.3.4.56');
        expect(element.val()).toEqual('12.3');
        expect($scope.value).toEqual('12.3');

        setVal(element, '12..34.56');
        expect(element.val()).toEqual('12.');
        expect($scope.value).toEqual('12.');
    });

    it('adds missing decimal places when it loses focus', function () {
        var element = prepareElement();

        setVal(element, '1234', true);
        expect(element.val()).toEqual('1,234.00');
        expect($scope.value).toEqual('1234');

        setVal(element, '1234.', true);
        expect(element.val()).toEqual('1,234.00');
        expect($scope.value).toEqual('1234.');

        setVal(element, '1234.1', true);
        expect(element.val()).toEqual('1,234.10');
        expect($scope.value).toEqual('1234.1');

        setVal(element, '1234.12', true);
        expect(element.val()).toEqual('1,234.12');
        expect($scope.value).toEqual('1234.12');
    });

    it('allows leading zeros in integer part', function () {
        var element = prepareElement();

        setVal(element, '0012');
        expect(element.val()).toEqual('0,012');
        expect($scope.value).toEqual('0012');
    });

    it('ignores all characters except numbers and dot', function () {
        var element = prepareElement();

        setVal(element, '100bb,21-2a.40');
        expect(element.val()).toEqual('100,212.40');
        expect($scope.value).toEqual('100212.40');
    });
});
