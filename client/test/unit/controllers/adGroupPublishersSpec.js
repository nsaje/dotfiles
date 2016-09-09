/* global module,beforeEach,it,describe,expect,inject,spyOn */
'use strict';

describe('AdGroupPublishersCtrl', function () {
    var $scope, $q, api;
    var permissions;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(module(function ($provide) {
        $provide.value('zemLocalStorageService', {get: function () {}});
        $provide.value('zemFilterService', {setShowBlacklistedPublishers: function () {}});
    }));

    beforeEach(function () {
        inject(function ($rootScope, $controller, _$q_) {
            $q = _$q_;
            $scope = $rootScope.$new();

            $scope.infoboxHeader = null;
            $scope.infoboxBasicSettings = null;
            $scope.infoboxPerformanceSettings = null;
            permissions = {};

            $scope.setActiveTab = function () {};
            $scope.isPermissionInternal = function () {
                return true;
            };
            $scope.hasPermission = function (permission) {
                if (!permissions.hasOwnProperty(permission)) return true;
                return permissions[permission];
            };
            $scope.setInfoboxHeader = function (data) {
                $scope.infoboxHeader = data;
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
            $scope.adGroupData = {
                1: {},
            };
            $scope.dateRange = {
                startDate: {
                    isValid: function () {},
                    isSame: function () {},
                },
                endDate: {
                    isValid: function () {},
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
                adGroupPublishersTable: {
                    get: mockApiFunc,
                },
                dailyStats: {
                    listPublishersStats: mockApiFunc,
                },
                adGroupOverview: {
                    get: mockApiFunc,
                },
            };
        });
    });

    function initializeController () {
        inject(function ($controller, $state) {
            $state.params = {id: 1};
            $controller('AdGroupPublishersCtrl', {
                $scope: $scope,
                $state: $state,
                api: api,
            });
        });
    }

    describe('getInfoboxData', function () {
        it('fetch infobox data with permission', function () {
            initializeController();
            spyOn(api.adGroupOverview, 'get').and.callFake(function () {
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
