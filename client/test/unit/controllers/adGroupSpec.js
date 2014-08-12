'use strict';

describe('AdGroupCtrl', function () {
    var $scope, ctrl, $state;

    beforeEach(function () {
        module('one');

        inject(function ($rootScope, $controller, _$state_) {
            $scope = $rootScope.$new();
            $scope.hasPermission = function () {
                return true;
            };
            $scope.adGroupData = {};

            $state = _$state_;
            ctrl = $controller('AdGroupCtrl', {$scope: $scope, $state: $state});
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
            $scope.adGroupData = {};
            $scope.setAdGroupData('key2', 'value2');
            expect($scope.adGroupData).toEqual({
                1: {
                    key2: 'value2'
                }
            });
        });
    });
});
