'use strict';

describe('MainCtrl', function () {
    var $scope, ctrl, $state;

    beforeEach(function () {
        module('one');

        module(function ($provide) {
            $provide.value('zemMoment', function () {
                return moment('2013-02-08T09:30:26.123+01:00');
            });
        });

        inject(function ($rootScope, $controller, _$state_) {
            $scope = $rootScope.$new();
            $state = _$state_;
            ctrl = $controller('MainCtrl', {$scope: $scope, $state: $state});
        });
    });

    it('should init accounts to null', function () {
        expect($scope.accounts).toBe(null);
    });

    describe('hasPermission', function () {
        beforeEach(function () {
            $scope.user = { permissions: [] };
        });

        it('should return true if user has the specified permission', function () {
            $scope.user.permissions.push('somePermission');
            expect($scope.hasPermission('somePermission')).toBe(true);
        });

        it('should return false if user does not have the specified permission', function () {
            expect($scope.hasPermission('somePermission')).toBe(false);
        });

        it('should return false if called without specifying permission', function () {
            expect($scope.hasPermission()).toBe(false);
        });
    });

    describe('setAdGroupData', function () {
        beforeEach(function () {
            $state.params.id = 1;
        });

        it('should add key-value pair for the current ad group', function () {
            $scope.adGroupData = { 1: { key1: 'value1' } };
            $scope.setAdGroupData('key2', 'value2');
            expect($scope.adGroupData).toEqual({
                1: {
                    key1: 'value1',
                    key2: 'value2'
                }
            });
        });

        it('should store key-value pair for the current ad group even when nothing has been stored yet', function () {
            $scope.setAdGroupData('key2', 'value2');
            expect($scope.adGroupData).toEqual({
                1: {
                    key2: 'value2'
                }
            });
        });
    });
});
