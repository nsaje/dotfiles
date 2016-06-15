/* global module,beforeEach,it,describe,expect,inject,spyOn */
'use strict';

describe('AllAccountsAccountsCtrl', function () {
    var $scope, $state, $q, api;
    var revokedPermissions;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(module(function ($provide) {
        $provide.value('zemLocalStorageService', {get: function () {}});
    }));

    // Replace DataSource Endpoint service with mocked one
    beforeEach(function () {
        var zemDataSourceDebugEndpoints;
        module(function ($provide) {
            $provide.value('zemDataSourceEndpoints', {
                getControllerMetaData: function () {
                    return {};
                },
                createAllAccountsEndpoint: function () {
                    return zemDataSourceDebugEndpoints.createMockEndpoint();
                },
            });
        });

        inject(function (_zemDataSourceDebugEndpoints_) {
            zemDataSourceDebugEndpoints = _zemDataSourceDebugEndpoints_;
        });
    });

    beforeEach(function () {
        inject(function ($rootScope, $controller, zemLocalStorageService, _$state_, _$q_) {
            $q = _$q_;
            $scope = $rootScope.$new();
            revokedPermissions = [];

            $scope.isPermissionInternal = function () {
                return true;
            };
            $scope.hasPermission = function (permission) {
                return revokedPermissions.indexOf(permission) === -1;
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
            };

            $state = _$state_;
            $state.params = {id: 1};

        });
    });

    function initializeController () {
        inject(function ($controller) {
            $controller('AllAccountsAccountsCtrl',
                {
                    $scope: $scope,
                    api: api,
                });
        });
    }

    describe('Zem-Grid DataSource', function () {
        it('check with no permission', function () {
            revokedPermissions.push('zemauth.can_access_table_breakdowns_development_features');
            initializeController();
            expect($scope.dataSource).toBe(undefined);
        });

        it('check with permission', function () {
            initializeController();
            expect($scope.dataSource).not.toBe(undefined);
        });
    });

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
