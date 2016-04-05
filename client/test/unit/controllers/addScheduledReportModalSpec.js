'use strict';

describe('AddScheduledReportModalCtrl', function () {
    var $scope, $modalInstance, api, $q, openedDeferred;
    var zemFilterServiceMock;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(module(function ($provide) {
        zemFilterServiceMock = {
            getShowArchived: function () { return true; },
            isSourceFilterOn: function () { return false; },
            getFilteredSources: function () {}
        };
        $provide.value('zemFilterService', zemFilterServiceMock);
    }));


    beforeEach(inject(function ($controller, $rootScope, _$q_) {
        $q = _$q_;
        $scope = $rootScope.$new();
        $scope.startDate = moment('2015-01-12');
        $scope.endDate = moment('2015-01-19');
        $scope.order = '-cost';
        $scope.baseUrl = 'test/';
        $scope.exportSchedulingFrequencies = [{value: 'weekly'}];
        $scope.options = [{value: 'view-csv'}];
        $scope.defaultOption = $scope.options[0]
        $scope.columns = [
            {field: 'cost', shown: true, checked: true, unselectable: false},
            {field: 'impressions', shown: true, checked: true, unselectable: false}
        ];
        var $state = {params: {id: 1}};
        $scope.level = 0;
        $scope.exportSources = undefined;
        openedDeferred = $q.defer();
        $modalInstance = {
            close: function () {},
            opened: openedDeferred.promise
        };
        $scope.isPermissionInternal = function () { return true; };
        $scope.hasPermission = function () { return true; };
        $scope.getAdditionalColumns = function () { return []; };
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
                addScheduledReport: mockApiFunc
            },
            exportPlusAllowed: {
                get: mockApiFunc
            }
        };

        $controller(
            'AddScheduledReportModalCtrl',
            {$scope: $scope, $modalInstance: $modalInstance, api: api, $state: $state}
        );
    }));

    describe('addScheduledReport', function () {
        it('updates validationErrors object on known errors', function () {
            var deferred = $q.defer();

            spyOn(api.scheduledReports, 'addScheduledReport').and.callFake(function () {
                return deferred.promise;
            });

            spyOn($modalInstance, 'close');
            $scope.init();
            $scope.addScheduledReport();
            $scope.$digest();

            expect(api.scheduledReports.addScheduledReport).toHaveBeenCalledWith(
                'test/export_plus/',
                {
                    type: 'view-csv',
                    start_date : moment('2015-01-12').format(),
                    end_date : moment('2015-01-19').format(),
                    order: '-cost',
                    by_day: false,
                    additional_fields: '',
                    filtered_sources: '',
                    frequency: 'daily',
                    recipient_emails: undefined,
                    report_name: undefined,
                    include_model_ids: undefined
                }
            );
            expect($scope.showInProgress).toBe(true);
            expect($modalInstance.close).not.toHaveBeenCalled();
            expect($scope.hasError).toEqual(false);
            expect($scope.validationErrors).toEqual({});

            deferred.reject({'err': ['Error']});
            $scope.$digest();

            expect($scope.showInProgress).toBe(false);
            expect($modalInstance.close).not.toHaveBeenCalled();
            expect($scope.hasError).toEqual(false);
            expect($scope.validationErrors).toEqual({'err': ['Error']});
        });

        it('updates error flag on unknown error', function () {
            var deferred = $q.defer();

            spyOn(api.scheduledReports, 'addScheduledReport').and.callFake(function () {
                return deferred.promise;
            });

            spyOn($modalInstance, 'close');

            $scope.init();
            $scope.addScheduledReport();
            $scope.$digest();

            expect(api.scheduledReports.addScheduledReport).toHaveBeenCalledWith(
              'test/export_plus/',
                {
                    type: 'view-csv',
                    start_date : moment('2015-01-12').format(),
                    end_date : moment('2015-01-19').format(),
                    order: '-cost',
                    by_day: false,
                    additional_fields: '',
                    filtered_sources: '',
                    frequency: 'daily',
                    recipient_emails: undefined,
                    report_name: undefined,
                    include_model_ids: undefined
                }
            );
            expect($scope.showInProgress).toBe(true);
            expect($modalInstance.close).not.toHaveBeenCalled();
            expect($scope.hasError).toEqual(false);
            expect($scope.validationErrors).toEqual({});

            deferred.reject(null);
            $scope.$digest();

            expect($scope.showInProgress).toBe(false);
            expect($modalInstance.close).not.toHaveBeenCalled();
            expect($scope.hasError).toEqual(true);
            expect($scope.validationErrors).toEqual({});
        });

        it('closes the modal window on success', function () {
            var deferred = $q.defer();

            spyOn(api.scheduledReports, 'addScheduledReport').and.callFake(function () {
                return deferred.promise;
            });

            spyOn($modalInstance, 'close');

            $scope.init();
            $scope.addScheduledReport();
            $scope.$digest();

            expect(api.scheduledReports.addScheduledReport).toHaveBeenCalledWith(
              'test/export_plus/',
                {
                    type: 'view-csv',
                    start_date : moment('2015-01-12').format(),
                    end_date : moment('2015-01-19').format(),
                    order: '-cost',
                    by_day: false,
                    additional_fields: '',
                    filtered_sources: '',
                    frequency: 'daily',
                    recipient_emails: undefined,
                    report_name: undefined,
                    include_model_ids: undefined
                }

            );
            expect($scope.showInProgress).toBe(true);
            expect($modalInstance.close).not.toHaveBeenCalled();

            deferred.resolve();
            $scope.$digest();

            expect($scope.showInProgress).toBe(false);
            expect($modalInstance.close).toHaveBeenCalled();
        });
    });
});
