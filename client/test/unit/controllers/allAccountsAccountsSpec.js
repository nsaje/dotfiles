/*global module,beforeEach,it,describe,expect,inject,spyOn*/
'use strict';

describe('AllAccountsAccountsCtrl', function () {
    var $modalStack, $scope, $state, $q, api, controller;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(module(function ($provide) {
        $provide.value('zemLocalStorageService', {get: function () {}});
    }));

    beforeEach(function () {
        inject(function ($rootScope, $controller, zemLocalStorageService, _$state_, _$q_, _$modalStack_) {
            $q = _$q_;
            $scope = $rootScope.$new();

            $scope.isPermissionInternal = function () {
                return true;
            };
            $scope.hasPermission = function () {
                return true;
            };
            $scope.hasInfoboxPermission = function () {
                return false;
            };
            $scope.getTableData = function () {
                return;
            };
            $scope.reflowGraph = function () {
                return;
            };
            $scope.setModels = function () {
                return;
            };
            $scope.dateRange = {
                startDate: {
                    isSame: function () {},
                },
                endDate: {
                    isSame: function () {},
                },
            };

            var mockApiFunc = function () {
                return {
                    then: function () {
                        return {
                            finally: function () {},
                        };
                    },
                };
            };

            api = {
                dailyStats: {
                    list: mockApiFunc,
                },
                accountAccountsTable: {
                    get: mockApiFunc,
                },
                allAccountsOverview: {
                    get: mockApiFunc,
                },
            }

            $state = _$state_;
            $state.params = {id: 1};

            $modalStack = _$modalStack_;

            controller = $controller('AllAccountsAccountsCtrl',
                {
                    $scope: $scope,
                    api: api,
                }
            );
        });
    });

    describe('no permission for infobox data', function () {
        it('fetch infobox data without permission', function () {
            $scope.getInfoboxData();
            $scope.$digest();
            expect($scope.infoboxHeader).toEqual(
                null
            );
        });
    });

    describe('getInfoboxData', function () {
        it('fetch infobox data with permission', function () {
            spyOn(api.allAccountsOverview, 'get').and.callFake(function () {
                var deferred = $q.defer();
                deferred.resolve(
                    {
                        header: {
                            title: 'Test',
                        },
                        basicSettings: {},
                        performanceSettings: {},
                    }
                );
                return deferred.promise;
            });

            $scope.hasInfoboxPermission = function () {
                return true;
            };
            $scope.getInfoboxData();
            $scope.$digest();
            expect($scope.infoboxHeader).toEqual(
                {
                    title: 'Test',
                }
            );
        });
    });
});
