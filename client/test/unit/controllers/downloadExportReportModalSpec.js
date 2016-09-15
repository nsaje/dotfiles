'use strict';

describe('DownloadExportReportModalCtrl', function () {
    var $scope, api, $q, openedDeferred, $window;
    var zemFilterServiceMock;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(module(function ($provide) {
        zemFilterServiceMock = {
            getShowArchived: function () { return true; },
            isSourceFilterOn: function () { return false; },
            isAgencyFilterOn: function () { return false; },
            isAccountTypeFilterOn: function () { return false; },
            getFilteredSources: function () {}
        };
        $provide.value('zemFilterService', zemFilterServiceMock);
    }));


    beforeEach(inject(function ($controller, $rootScope, _$q_, zemDataFilterService) {
        $q = _$q_;
        $scope = $rootScope.$new();
        $scope.$close = function () {};
        zemDataFilterService.setDateRange({
            startDate: moment.utc('2015-01-12'),
            endDate: moment.utc('2015-01-19'),
        });
        $scope.order = '-cost';
        $scope.baseUrl = 'test/';
        $scope.options = [{value: 'view-csv'}];
        $scope.defaultOption = $scope.options[0];
        var $state = {params: {id: 1}};
        $scope.level = 0;
        $scope.exportSources = undefined;

        $window = {
            open: function () {}
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
            exportAllowed: {
                get: mockApiFunc
            }
        };

        $controller(
            'DownloadExportReportModalCtrl',
            {$scope: $scope, api: api, $state: $state, $window: $window}
        );
    }));

    describe('DownloadExportReportModalCtrl', function () {
        it('closes the modal window on download', function () {
            var deferred = $q.defer();

            spyOn($scope, '$close');

            $scope.init();
            $scope.downloadReport();
            $scope.$digest();

            expect($scope.$close).toHaveBeenCalled();
        });

        it('tests checkDownloadAllowed', function () {
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
        it('tests downloadReport', function () {
            var deferred = $q.defer();
            spyOn($window, 'open');
            $scope.init();
            $scope.isPermissionInternal = function () { return true; };
            $scope.hasPermission = function () { return true; };
            $scope.downloadReport();
            $scope.$digest();

            expect($window.open).toHaveBeenCalledWith(
              'test/export/?type=view-csv&start_date=2015-01-12T00:00:00Z&end_date=2015-01-19T00:00:00Z&order=-cost&by_day=undefined&include_model_ids=undefined&include_totals=undefined&additional_fields=',
              '_blank');
        });
    });
});
