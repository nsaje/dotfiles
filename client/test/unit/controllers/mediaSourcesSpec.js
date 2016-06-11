/* global module,beforeEach,it,describe,expect,inject,spyOn,constants */
'use strict';

describe('MediaSourcesCtrl', function () {
    var $scope, $state, $q, api;
    var permissions;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(module(function ($provide, zemDataSourceDebugEndpointsProvider) {
        $provide.value('zemLocalStorageService', {get: function () { }});
        $provide.value('zemDataSourceEndpoints', zemDataSourceDebugEndpointsProvider.$get());
    }));

    beforeEach(function () {
        inject(function ($rootScope, $controller, zemLocalStorageService, _$state_, _$q_) {
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

            $state = _$state_;
            $state.params = {id: 1};

        });
    });

    function initializeController () {
        inject(function ($controller) {
            $controller('MediaSourcesCtrl',
                {
                    $scope: $scope,
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

    describe('Zem-Grid DataSource', function () {
        it('check without permission', function () {
            permissions['zemauth.can_access_table_breakdowns_development_features'] = false;
            initializeController();
            expect($scope.dataSource).toBe(undefined);
        });

        it('check with permission', function () {
            initializeController();
            expect($scope.dataSource).not.toBe(undefined);
        });
    });
});
