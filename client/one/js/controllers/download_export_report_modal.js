/* globals oneApp, constants */
oneApp.controller('DownloadExportReportModalCtrl', ['$scope', '$modalInstance', 'api', 'zemFilterService', '$window', '$state', function ($scope, $modalInstance, api, zemFilterService, $window, $state) {  // eslint-disable-line max-len
    $scope.showInProgress = false;
    $scope.export = {};

    $scope.setDisabledExportOptions = function () {
        $scope.showInProgress = true;
        api.exportPlusAllowed.get($state.params.id, $scope.level,
            $scope.exportSources, $scope.startDate, $scope.endDate).then(
            function (data) {
                $scope.options.forEach(function (opt) {
                    if (opt.value === constants.exportType.CONTENT_AD) {
                        opt.disabled = !data.content_ad;
                        opt.disabledByDay = !data.byDay.content_ad;
                    } else if (opt.value === constants.exportType.AD_GROUP) {
                        opt.disabled = !data.ad_group;
                        opt.disabledByDay = !data.byDay.ad_group;
                    } else if (opt.value === constants.exportType.CAMPAIGN) {
                        opt.disabled = !data.campaign;
                        opt.disabledByDay = !data.byDay.campaign;
                    } else if (opt.value === constants.exportType.ACCOUNT) {
                        opt.disabled = !data.account;
                        opt.disabledByDay = !data.byDay.account;
                    } else if (opt.value === constants.exportType.ALL_ACCOUNTS) {
                        opt.disabled = !data.all_accounts;
                        opt.disabledByDay = !data.byDay.all_accounts;
                    }
                });
            }
        ).finally(function () {
            $scope.checkDownloadAllowed();
            $scope.showInProgress = false;
        });
    };

    $scope.checkDownloadAllowed = function () {
        var option = getOptionByValue($scope.export.type.value);
        $scope.downloadAllowed = true;
        $scope.downloadNotAllowedMessage = '';

        if (option.disabledByDay && $scope.export.byDay) {
            $scope.downloadNotAllowedMessage = 'Please select shorter date range to download report ' +
                'with breakdown by day.';
            $scope.downloadAllowed = false;
        }
        if (option.disabled) {
            $scope.downloadNotAllowedMessage = 'This report is not available for download due to the ' +
                'volume of content. Please select shorter date range or different granularity.';
            $scope.downloadAllowed = false;
        }
    };

    $scope.downloadReport = function () {
        var url = $scope.baseUrl + 'export_plus/?type=' + $scope.export.type.value +
            '&start_date=' + $scope.startDate.format() +
            '&end_date=' + $scope.endDate.format() +
            '&order=' + $scope.order +
            '&by_day=' + $scope.export.byDay;

        if ($scope.hasPermission('zemauth.can_include_model_ids_in_reports')) {
            url += '&include_model_ids=' + $scope.export.includeIds;
        }
        if (zemFilterService.isSourceFilterOn()) {
            url += '&filtered_sources=' + zemFilterService.getFilteredSources().join(',');
        }
        url += '&additional_fields=' + $scope.getAdditionalColumns().join(',');
        $window.open(url, '_blank');
        $modalInstance.close();
    };

    $scope.init = function () {
        $scope.export.type = $scope.options[0];
        for (var i = 1; i < $scope.options.length; ++i) {
            if ($scope.options[i].defaultOption) {
                $scope.export.type = $scope.options[i];
            }
        }
        $scope.setDisabledExportOptions();
    };
    $scope.init();

    function getOptionByValue (value) {
        var option = null;
        $scope.options.forEach(function (opt) {
            if (opt.value === value) {
                option = opt;
            }
        });
        return option;
    }
}]);
