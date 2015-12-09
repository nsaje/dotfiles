'use strict';

describe('AddScheduledReportModalCtrl', function() {
    var $scope, $modalInstance, api, $q, openedDeferred;
    var zemFilterServiceMock;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(module(function ($provide) {
        zemFilterServiceMock = {
            getShowArchived: function() { return true; },
            isSourceFilterOn: function() { return false; },
            getFilteredSources: function() {}
        };
        $provide.value('zemFilterService', zemFilterServiceMock);
    }));


    beforeEach(inject(function($controller, $rootScope, _$q_) {
        $q = _$q_;
        $scope = $rootScope.$new();
        $scope.startDate = moment('2015-01-12');
        $scope.endDate = moment('2015-01-19');
        $scope.order = '-cost';
        $scope.baseUrl = 'test/';
        $scope.exportSchedulingFrequencies = [{value: 'weekly'}];
        $scope.options = [{value: 'view-csv'}];
        $scope.columns = [
            { field: 'cost', shown: true, checked: true, unselectable: false },
            { field: 'impressions', shown: true, checked: true, unselectable: false }
        ];
        var $state = { params: { id: 1 } };
        $scope.level = 0;
        $scope.exportSources = undefined;
        openedDeferred = $q.defer();
        $modalInstance = {
            close: function(){},
            opened: openedDeferred.promise
        };

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

    describe('addScheduledReport', function() {
        it('updates validationErrors object on known errors', function() {
            var deferred = $q.defer();

            spyOn(api.scheduledReports, 'addScheduledReport').and.callFake(function() {
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
                    by_day: undefined,
                    additional_fields: 'cost,impressions',
                    filtered_sources: '',
                    frequency: 'daily',
                    recipient_emails: undefined,
                    report_name: undefined
                }
            );
            expect($scope.addScheduledReportInProgress).toBe(true);
            expect($modalInstance.close).not.toHaveBeenCalled();
            expect($scope.hasError).toEqual(false);
            expect($scope.validationErrors).toEqual({});

            deferred.reject({'err': ['Error']});
            $scope.$digest();

            expect($scope.addScheduledReportInProgress).toBe(false);
            expect($modalInstance.close).not.toHaveBeenCalled();
            expect($scope.hasError).toEqual(false);
            expect($scope.validationErrors).toEqual({'err': ['Error']});
        });

        it('updates error flag on unknown error', function () {
            var deferred = $q.defer();

            spyOn(api.scheduledReports, 'addScheduledReport').and.callFake(function() {
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
                  by_day: undefined,
                  additional_fields: 'cost,impressions',
                  filtered_sources: '',
                  frequency: 'daily',
                  recipient_emails: undefined,
                  report_name: undefined
              }
            );
            expect($scope.addScheduledReportInProgress).toBe(true);
            expect($modalInstance.close).not.toHaveBeenCalled();
            expect($scope.hasError).toEqual(false);
            expect($scope.validationErrors).toEqual({});

            deferred.reject(null);
            $scope.$digest();

            expect($scope.addScheduledReportInProgress).toBe(false);
            expect($modalInstance.close).not.toHaveBeenCalled();
            expect($scope.hasError).toEqual(true);
            expect($scope.validationErrors).toEqual({});
        });

        it('closes the modal window on success', function() {
            var deferred = $q.defer();

            spyOn(api.scheduledReports, 'addScheduledReport').and.callFake(function() {
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
                  by_day: undefined,
                  additional_fields: 'cost,impressions',
                  filtered_sources: '',
                  frequency: 'daily',
                  recipient_emails: undefined,
                  report_name: undefined
              }

            );
            expect($scope.addScheduledReportInProgress).toBe(true);
            expect($modalInstance.close).not.toHaveBeenCalled();

            deferred.resolve();
            $scope.$digest();

            expect($scope.addScheduledReportInProgress).toBe(false);
            expect($modalInstance.close).toHaveBeenCalled();
        });

        it('tests getAdditionalColumns', function() {

            expect($scope.getAdditionalColumns()).toEqual(['cost', 'impressions']);

            $scope.columns = [
                { field: 'cost', shown: false, checked: true, unselectable: false },
                { field: 'impressions', shown: true, checked: true, unselectable: false }
            ];
            expect($scope.getAdditionalColumns()).toEqual(['impressions']);

            $scope.columns = [
                { field: 'cost', shown: true, checked: false, unselectable: false },
                { field: 'impressions', shown: true, checked: true, unselectable: false }
            ];
            expect($scope.getAdditionalColumns()).toEqual(['impressions']);

            $scope.columns = [
                { field: 'cost', shown: false, checked: true, unselectable: false },
                { field: 'impressions', shown: false, checked: true, unselectable: false }
            ];
            expect($scope.getAdditionalColumns()).toEqual([]);
        });

        it('tests checkDownloadAllowed', function() {
            $scope.options = [
                {value: 'allOk', disabled: false, disabledByDay: false},
                {value: 'disabledByDay', disabled: false, disabledByDay: true},
                {value: 'disabledBoth', disabled: true, disabledByDay: true}
            ];

            $scope.export.type.value = 'allOk';
            $scope.export.byDay = true;
            $scope.checkDownloadAllowed();
            expect($scope.downloadNotAllowedMessage).toEqual('');
            expect($scope.downloadAllowed).toBe(true);
            $scope.export.byDay = false;
            $scope.checkDownloadAllowed();
            expect($scope.downloadNotAllowedMessage).toEqual('');
            expect($scope.downloadAllowed).toBe(true);

            $scope.export.type.value = 'disabledByDay';
            $scope.export.byDay = true;
            $scope.checkDownloadAllowed();
            expect($scope.downloadNotAllowedMessage).toEqual('Please select shorter date range to download report with breakdown by day.');
            expect($scope.downloadAllowed).toBe(false);

            $scope.export.type.value = 'disabledBoth';
            $scope.export.byDay = true;
            $scope.checkDownloadAllowed();
            expect($scope.downloadNotAllowedMessage).toEqual('This report is not available for download due to the volume of content. Please select shorter date range or different granularity.');
            expect($scope.downloadAllowed).toBe(false);

            $scope.export.byDay = false;
            $scope.checkDownloadAllowed();
            expect($scope.downloadNotAllowedMessage).toEqual('This report is not available for download due to the volume of content. Please select shorter date range or different granularity.');
            expect($scope.downloadAllowed).toBe(false);
        });
    });
});
