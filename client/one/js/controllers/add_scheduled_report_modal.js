/* globals oneApp, options, constants */
oneApp.controller('AddScheduledReportModalCtrl', ['$scope', '$modalInstance', 'api', 'zemFilterService', function ($scope, $modalInstance, api, zemFilterService) {  // eslint-disable-line max-len
    $scope.exportSchedulingFrequencies = options.exportFrequency;
    $scope.showInProgress = false;
    $scope.hasError = false;
    $scope.breakdownByDayDisabled = false;

    $scope.export = {};
    $scope.validationErrors = {};

    $scope.checkBreakdownAvailable = function () {
        $scope.breakdownByDayDisabled = false;
        if ($scope.export.frequency.value === constants.exportFrequency.DAILY) {
            $scope.breakdownByDayDisabled = true;
            $scope.export.byDay = false;
        }
    };

    $scope.addScheduledReport = function () {
        $scope.clearErrors();
        $scope.showInProgress = true;
        var url = $scope.baseUrl + 'export_plus/';
        var data = {
            'type': $scope.export.type.value,
            'start_date': $scope.startDate.format(),
            'end_date': $scope.endDate.format(),
            'order': $scope.order,
            'by_day': $scope.export.byDay,
            'additional_fields': $scope.getAdditionalColumns().join(','),
            'filtered_sources': zemFilterService.isSourceFilterOn() ?
                zemFilterService.getFilteredSources().join(',') : '',
            'frequency': $scope.export.frequency.value,
            'recipient_emails': $scope.export.recipientEmails,
            'report_name': $scope.export.reportName,
        };

        if ($scope.hasPermission('zemauth.can_include_model_ids_in_reports')) {
            data['&include_model_ids'] = $scope.export.includeIds;
        }

        api.scheduledReports.addScheduledReport(url, data).then(
            function (data) {
                $modalInstance.close();
            },
            function (errors) {
                if (errors) {
                    $scope.validationErrors = errors;
                } else {
                    $scope.hasError = true;
                }
            }
        ).finally(function () {
            $scope.showInProgress = false;
        });
    };

    $scope.clearErrors = function (name) {
        $scope.hasError = false;
        $scope.validationErrors = {};
    };

    $scope.init = function () {
        $scope.export.frequency = $scope.exportSchedulingFrequencies[0];
        $scope.export.type = $scope.options[0];
        $scope.checkBreakdownAvailable();
    };
    $scope.init();
}]);
