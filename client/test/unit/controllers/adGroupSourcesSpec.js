/* global module,beforeEach,it,describe,expect,inject,spyOn */
'use strict';

describe('AdGroupSourcesCtrlSpec', function () {
    var $scope, api, $timeout;
    var permissions;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(module(function ($provide) {
        $provide.value('zemLocalStorageService', {get: function () {}});
        $provide.value('zemCustomTableColsService', {
            load: function () { return []; },
            save: function () { return []; }
        });
    }));

    beforeEach(inject(function ($rootScope, _$timeout_) {
        $scope = $rootScope.$new();
        permissions = {};

        $scope.setActiveTab = function () {};
        $scope.isPermissionInternal = function () {
            return true;
        };
        $scope.hasPermission = function (permission) {
            if (!permissions.hasOwnProperty(permission)) return true;
            return permissions[permission];
        };
        $scope.setAdGroupData = function () {};
        $scope.adGroupData = {};
        $scope.columns = [];

        $timeout = _$timeout_;

        var mockApiFunc = function () {
            return {
                then: function () {
                    return {
                        finally: function () {}
                    };
                }
            };
        };

        api = {
            adGroupSourcesUpdates: {get: function () {}},
            adGroupSourcesTable: {get: function () {
                return {
                    then: function () {
                        return {finally: function () {}};
                    }
                };
            }},
            dailyStats: {list: function () {
                return {
                    then: function () { return this; },
                    finally: function () { return this; },
                    abort: function () {},
                };
            }},
            adGroupSources: {get: function () {
                return {
                    then: function () {}
                };
            }},
            sourcesExportAllowed: {
                get: mockApiFunc
            },
            adGroupOverview: {
                get: mockApiFunc
            },
            campaignOverview: {
                get: mockApiFunc
            }
        };
    }));

    function initializeController () {
        inject(function ($controller, $state) {
            $state.params = {id: 123};
            $controller('AdGroupSourcesCtrl', {$scope: $scope, api: api, $state: $state});
        });
    }

    describe('pollSourcesTableUpdates', function () {
        beforeEach(function () {
            initializeController();
        });
        it('returns early if lastChangeTimeout is set', function () {
            spyOn(api, 'adGroupSourcesUpdates');
            $scope.lastChangeTimeout = 123;

            $scope.pollSourcesTableUpdates();

            expect(api.adGroupSourcesUpdates).not.toHaveBeenCalled();
        });

        it('updates data if lastChange is received', function () {
            $scope.rows = [{id: 12, cpc: '0.300'}];
            $scope.totals = {cpc: '1.200'};

            var data = {
                lastChange: 1000,
                notifications: 'some notifications',
                dataStatus: 'data status',
                rows: {12: {cpc: '0.444'}},
                totals: {cpc: '2.300'}
            };

            api.adGroupSourcesUpdates = {
                get: function () {
                    return {
                        then: function (handler) {
                            handler(data);
                        }
                    };
                }
            };

            $scope.pollSourcesTableUpdates();

            expect($scope.lastChange).toEqual(data.lastChange);
            expect($scope.notifications).toEqual(data.notifications);
            expect($scope.dataStatus).toEqual(data.dataStatus);

            expect($scope.rows[0].cpc).toEqual(data.rows[12].cpc);
            expect($scope.totals.cpc).toEqual(data.totals.cpc);
        });

        it('schedules another poll if in progress', function () {
            $scope.rows = [{id: 12, cpc: '0.300'}];
            $scope.totals = {cpc: '1.200'};

            var data = {inProgress: true};

            api.adGroupSourcesUpdates = {
                get: function () {
                    return {
                        then: function (handler) {
                            handler(data);
                        }
                    };
                }
            };

            $scope.pollSourcesTableUpdates();

            spyOn($scope, 'pollSourcesTableUpdates');
            $timeout.flush();

            expect($scope.lastChangeTimeout).toBe(null);
            expect($scope.pollSourcesTableUpdates).toHaveBeenCalled();
        });

        it('should leave selected metrics when they are not conversion goals', function () {
            $scope.chartMetric1 = 'ctr';
            $scope.chartMetric2 = 'cpc';

            var data = {
                chartData: [],
                conversionGoals: []
            };

            api.dailyStats = {
                list: function () {
                    return {
                        then: function (handler) {
                            handler(data);
                            return this;
                        },
                        finally: function () {},
                    };
                }
            };

            $scope.getDailyStats();

            expect($scope.chartMetric1).toBe('ctr');
            expect($scope.chartMetric2).toBe('cpc');
        });

    });

    it('should select default metrics when conversion goals don\'t exist', function () {
        initializeController();
        $scope.chartMetric1 = 'conversion_goal_1';
        $scope.chartMetric2 = 'conversion_goal_2';

        var data = {
            chartData: [],
            conversionGoals: []
        };

        api.dailyStats = {
            list: function () {
                return {
                    then: function (handler) {
                        handler(data);
                        return this;
                    },
                    finally: function () {},
                };
            }
        };

        $scope.getDailyStats();

        expect($scope.chartMetric1).toBe('clicks');
        expect($scope.chartMetric2).toBe('impressions');
    });
});
