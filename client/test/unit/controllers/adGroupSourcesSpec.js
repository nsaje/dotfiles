'use strict';

describe('AdGroupSourcesCtrl', function() {
    var $scope, api, $timeout;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(module(function ($provide) {
        $provide.value('zemLocalStorageService', {get: function(){}});
        $provide.value('zemCustomTableColsService', {
            load: function() {return [];},
            save: function() {return [];}
        });
        $provide.value('zemPostclickMetricsService', {
            insertAcquisitionColumns: function(){},
            insertEngagementColumns: function(){},
            concatAcquisitionChartOptions: function(){return [];},
            concatEngagementChartOptions: function(){return [];}
        });
    }));

    beforeEach(inject(function($rootScope, $controller, _$timeout_, $state) {
        $scope = $rootScope.$new();
        $scope.isPermissionInternal = function() {return true;};
        $scope.hasPermission = function() {return true;};
        $scope.setAdGroupData = function() {};
        $scope.getAdGroupState = function() {};
        $scope.adGroupData = {};
        $scope.dateRange = {
            startDate: {isSame: function() {}},
            endDate: {isSame: function() {}}
        };
        $scope.columns = [];

        $timeout = _$timeout_;

        var mockApiFunc = function() {
            return {
                then: function() {
                    return {
                        finally: function() {}
                    };
                }
            };
        };

        api = {
            adGroupSourcesUpdates: {get: function() {}},
            adGroupSourcesTable: {get: function() {
                return {
                    then: function() {
                        return {finally: function() {}}
                    }
                }
            }},
            dailyStats: {list: function() {
                return {
                    then: function() {}
                }
            }},
            adGroupSources: {get: function() {
                return {
                    then: function() {}
                }
            }},
            sourcesExportPlusAllowed: {
                get: mockApiFunc
            }
        };

        $state.params = {id: 123};
        $controller('AdGroupSourcesCtrl', {$scope: $scope, api: api, $state: $state});
    }));

    describe('pollSourcesTableUpdates', function() {
        it('returns early if user doesn\'t have permission', function() {
            $scope.hasPermission = function() {return false;};
            spyOn(api, 'adGroupSourcesUpdates');

            $scope.pollSourcesTableUpdates();

            expect(api.adGroupSourcesUpdates).not.toHaveBeenCalled();
        });

        it('returns early if lastChangeTimeout is set', function() {
            spyOn(api, 'adGroupSourcesUpdates');
            $scope.lastChangeTimeout = 123;

            $scope.pollSourcesTableUpdates();

            expect(api.adGroupSourcesUpdates).not.toHaveBeenCalled();
        });

        it('updates data if lastChange is received', function() {
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
                get: function() {
                    return {
                        then: function(handler) {
                            handler(data);
                        }
                    }
                }
            };

            $scope.pollSourcesTableUpdates();

            expect($scope.lastChange).toEqual(data.lastChange);
            expect($scope.notifications).toEqual(data.notifications);
            expect($scope.dataStatus).toEqual(data.dataStatus);

            expect($scope.rows[0].cpc).toEqual(data.rows[12].cpc);
            expect($scope.totals.cpc).toEqual(data.totals.cpc);
        });

        it('schedules another poll if in progress', function() {
            $scope.rows = [{id: 12, cpc: '0.300'}];
            $scope.totals = {cpc: '1.200'};

            var data = {inProgress: true};

            api.adGroupSourcesUpdates = {
                get: function() {
                    return {
                        then: function(handler) {
                            handler(data);
                        }
                    }
                }
            };

            $scope.pollSourcesTableUpdates();

            spyOn($scope, 'pollSourcesTableUpdates');
            $timeout.flush();

            expect($scope.lastChangeTimeout).toBe(null);
            expect($scope.pollSourcesTableUpdates).toHaveBeenCalled();
        });
    });
});
