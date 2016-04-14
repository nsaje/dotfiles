/* globals describe, it, inject, module, expect, beforeEach */
'use strict';

describe('zemNumericValidator', function () {
    var $scope, httpBackend, element;
    var template = '<input id="input" type="text" zem-numeric-validator ' +
        'ng-model="value" placeholder="0.00" maxlength="5" />';

    beforeEach(module('one'));
    beforeEach(inject(function ($compile, $rootScope, $httpBackend) {
        compile = $compile;
        $scope = $rootScope.$new();
        httpBackend = $httpBackend;
        $scope.isPermissionInternal = function () {
            return true; 
        };
        $scope.hasPermission = function () { 
            return true; 
        };

        httpBackend.when('GET', '/api/users/current/').respond({});
        httpBackend.when('GET', '/api/all_accounts/nav/').respond({});

        $scope.value = '0.001'

        element = $compile(template)($scope);

        $scope.$digest();
        isolate = element.isolateScope();
    }));

    it('validates a number', function () {
        element.val(0.001);
        element.trigger('input');
        $scope.$digest();
        $scope.$apply();
        expect($scope.value).toEqual('0.001');

        element.val(15000);
        element.trigger('input');
        $scope.$digest();
        $scope.$apply();
        expect($scope.value).toEqual('15000');
    });

    it('doesn\'t validate non-numbers', function () {
        element.val(10);
        element.trigger('input');
        $scope.$digest();
        $scope.$apply();
        expect(element.val()).toBe('10');
        
        element.val("abc");
        element.trigger('input');
        $scope.$digest();
        $scope.$apply();
        expect(element.val()).toBe('');
    });
});
