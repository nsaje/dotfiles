'use strict';

describe('DownloadExportReportModalCtrl', function () {
    var $scope, $modalInstance, api, $q, openedDeferred, $window;
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
        $scope.startDate = moment.utc('2015-01-12');
        $scope.endDate = moment.utc('2015-01-19');
        $scope.order = '-cost';
        $scope.baseUrl = 'test/';
        $scope.options = [{value: 'view-csv'}];
        $scope.defaultOption = $scope.options[0];
        var $state = {params: {id: 1}};
        $scope.level = 0;
        $scope.exportSources = undefined;
        openedDeferred = $q.defer();
        $modalInstance = {
            close: function () {},
            opened: openedDeferred.promise
        };
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
            exportPlusAllowed: {
                get: mockApiFunc
            }
        };

        $controller(
            'DownloadExportReportModalCtrl',
            {$scope: $scope, $modalInstance: $modalInstance, api: api, $state: $state, $window: $window}
        );
    }));

    describe('DownloadExportReportModalCtrl', function () {
        it('closes the modal window on download', function () {
            var deferred = $q.defer();

            spyOn($modalInstance, 'close');

            $scope.init();
            $scope.downloadReport();
            $scope.$digest();

            expect($modalInstance.close).toHaveBeenCalled();
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
              'test/export/?type=view-csv&start_date=2015-01-12T00:00:00+00:00&end_date=2015-01-19T00:00:00+00:00&order=-cost&by_day=undefined&include_model_ids=undefined&additional_fields=',
              '_blank');
        });
    });
});
