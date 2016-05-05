/* global module,beforeEach,it,describe,expect,inject,spyOn */
'use strict';

describe('AccountAccountCtrl', function () {
    var $scope, $state, $q, api;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(function () {
        inject(function ($rootScope, $controller, _$state_, _$q_) {
            $q = _$q_;
            $scope = $rootScope.$new();

            $scope.isPermissionInternal = function () {
                return true;
            };
            $scope.hasPermission = function () {
                return true;
            };
            $scope.account = {id: 1};

            var mockApiFunc = function () {
                return {
                    then: function () {
                        return {
                            finally: function () {},
                        };
                    }
                };
            };

            api = {
                accountAgency: {
                    get: mockApiFunc,
                },
                accountUsers: {
                    list: mockApiFunc,
                },
            };

            $state = _$state_;
            $state.params = {id: 1};

            $controller('AccountAccountCtrl', {$scope: $scope, api: api});
        });
    });

    describe('allowedMediaSources', function () {
        beforeEach(function () {
            $scope.settings.allowedSources = {
                '1': {name: 'source 1'},
                '2': {name: 'source 2', allowed: true},
                '3': {name: 'source 3', allowed: false},
            };
            $scope.selectedMediaSources = {allowed: [], available: []};
        });

        it('gets allowed media sources', function () {
            expect($scope.getAllowedMediaSources()).toEqual([
                {name: 'source 2', allowed: true, value: '2'}
            ]);
        });

        it('gets available media sources', function () {
            var available = $scope.getAvailableMediaSources();

            expect(available).toContain({name: 'source 1', value: '1'});
            expect(available).toContain({name: 'source 3', value: '3', allowed: false});
        });

        it('adds to allowed media sources', function () {
            $scope.selectedMediaSources.available = ['1'];
            $scope.addToAllowedMediaSources();
            expect($scope.settings.allowedSources['1'].allowed).toBe(true);
            expect($scope.selectedMediaSources.available).toEqual([]);
        });

        it('removes from allowed media sources', function () {
            $scope.selectedMediaSources.allowed = ['2'];
            $scope.removeFromAllowedMediaSources();
            expect($scope.settings.allowedSources['2'].allowed).toBe(false);
            expect($scope.selectedMediaSources.allowed).toEqual([]);
        });
    });
});
