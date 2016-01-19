'use strict';

describe('ScheduledReportsCtrl', function () {
    var $scope, $state, $q, api;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(function () {
        inject(function ($rootScope, $controller, _$state_, _$q_, _$modalStack_) {
            $q = _$q_;
            $scope = $rootScope.$new();

            $scope.isPermissionInternal = function () { return true; };
            $scope.hasPermission = function () { return true; };
            $scope.account = {id: 1};
            $scope.reports = [];

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
                scheduledReports: {
                    get: mockApiFunc,
                    put: mockApiFunc
                }
            };

            $state = _$state_;
            $state.params = {id: 1};

            $controller('ScheduledReportsCtrl', {$scope: $scope, api: api});
        });
    });


    describe('getReports', function () {
        beforeEach(function () {
            $scope.reports = [];
        });

        it('displays error on failure', function () {
            var deferred = $q.defer();

            spyOn(api.scheduledReports, 'get').and.callFake(function () {
                return deferred.promise;
            });

            $scope.getReports();
            $scope.$digest();

            expect($scope.requestInProgress).toBe(true);

            deferred.reject();
            $scope.$digest();

            expect($scope.requestInProgress).toBe(false);
            expect(api.scheduledReports.get).toHaveBeenCalled();
            expect($scope.reports).toEqual([]);
            expect($scope.errorMessage).toEqual('Error Retrieving Reports');
        });

        it('populates reports array on success', function () {
            var deferred = $q.defer();

            spyOn(api.scheduledReports, 'get').and.callFake(function () {
                return deferred.promise;
            });

            $scope.getReports();
            $scope.$digest();

            expect($scope.requestInProgress).toBe(true);
            var reports = {reports: [
                {
                    frequency: 'Daily',
                    granularity: 'Content Ad, by Media Source',
                    level: 'Ad Group',
                    name: 'Rep1',
                    recipients: 'test@zemanta.com',
                    scheduled_report_id: 1
                }, {
                    frequency: 'Weekly',
                    granularity: 'Ad Group',
                    level: 'Campaign',
                    name: 'Rep2',
                    recipients: 'test2@zemanta.com,test3@zemanta.com',
                    scheduled_report_id: 2
                }
            ]};
            deferred.resolve(reports);
            $scope.$digest();

            expect($scope.requestInProgress).toBe(false);
            expect(api.scheduledReports.get).toHaveBeenCalled();
            expect($scope.reports).toEqual(reports.reports);
            expect($scope.errorMessage).toEqual('');
        });
    });
});
