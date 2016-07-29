/* global module,beforeEach,it,describe,expect,inject,spyOn,constants */
'use strict';

describe('MediaSourcesCtrl', function () {
    var $scope, $q, api;
    var permissions;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(module(function ($provide) {
        $provide.value('zemLocalStorageService', {get: function () { }});
    }));

    beforeEach(function () {
        inject(function ($rootScope, _$q_) {
            $q = _$q_;
            $scope = $rootScope.$new();
            permissions = {};

            $scope.isPermissionInternal = function () {
                return true;
            };
            $scope.hasPermission = function (permission) {
                if (!permissions.hasOwnProperty(permission)) return true;
                return permissions[permission];
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
                    isSame: function () {
                    },
                },
                endDate: {
                    isSame: function () {
                    },
                },
            };
            $scope.level = constants.level.ALL_ACCOUNTS;

            var mockApiFunc = function () {
                return {
                    then: function () {
                        return {
                            finally: function () {
                            },
                        };
                    },
                    abort: function () {
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
                sourcesTable: {
                    get: mockApiFunc,
                },
            };
        });
    });

    function initializeController () {
        inject(function ($controller, $state) {
            $state.params = {id: 1};
            $controller('MediaSourcesCtrl',
                {
                    $scope: $scope,
                    $state: $state,
                    api: api,
                }
            );
        });
    }

    describe('getInfoboxData', function () {
        it('fetch infobox data', function () {
            initializeController();
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
