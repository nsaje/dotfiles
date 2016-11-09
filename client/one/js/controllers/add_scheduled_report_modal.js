/* globals angular, options, constants */
angular.module('one.legacy').controller('AddScheduledReportModalCtrl', function ($scope, api, zemFilterService, zemDataFilterService) {  // eslint-disable-line max-len
    $scope.exportSchedulingFrequencies = options.exportFrequency;
    $scope.exportSchedulingTimePeriods = options.exportTimePeriod;
    $scope.exportSchedulingDayOfWeek = options.exportDayOfWeek;
    $scope.showInProgress = false;
    $scope.hasError = false;
    $scope.breakdownByDayDisabled = false;
    $scope.dayOfWeekShown = false;

    $scope.export = {};
    $scope.validationErrors = {};

    $scope.timePeriodChanged = function () {
        $scope.breakdownByDayDisabled = false;
        if ($scope.export.timePeriod.value === constants.exportTimePeriod.YESTERDAY) {
            $scope.breakdownByDayDisabled = true;
            $scope.export.byDay = false;
        }
    };

    $scope.frequencyChanged = function () {
        $scope.dayOfWeekShown = false;
        if ($scope.export.frequency.value === constants.exportFrequency.WEEKLY) {
            $scope.dayOfWeekShown = true;
        }

        if (!$scope.hasPermission('zemauth.can_set_time_period_in_scheduled_reports')) {
            $scope.breakdownByDayDisabled = false;
            if ($scope.export.frequency.value === constants.exportFrequency.DAILY) {
                $scope.breakdownByDayDisabled = true;
                $scope.export.byDay = false;
            }
        }
    };

    $scope.addScheduledReport = function () {
        $scope.clearErrors();
        $scope.showInProgress = true;
        var url = $scope.baseUrl + 'export/';
        var dateRange = zemDataFilterService.getDateRange();
        var data = {
            'type': $scope.export.type.value,
            'start_date': dateRange.startDate.format(),
            'end_date': dateRange.endDate.format(),
            'order': $scope.order,
            'by_day': $scope.export.byDay,
            'additional_fields': $scope.getAdditionalColumns().join(','),
            'filtered_sources': zemFilterService.isSourceFilterOn() ?
                zemFilterService.getFilteredSources().join(',') : '',
            'frequency': $scope.export.frequency.value,
            'day_of_week': $scope.export.dayOfWeek.value,
            'time_period': $scope.export.timePeriod.value,
            'recipient_emails': $scope.export.recipientEmails,
            'report_name': $scope.export.reportName,
        };

        if (zemFilterService.isAgencyFilterOn()) {
            data.filtered_agencies = zemFilterService.getFilteredAgencies().join(',');
        }
        if (zemFilterService.isAccountTypeFilterOn()) {
            data.filtered_account_types = zemFilterService.getFilteredAccountTypes().join(',');
        }

        if ($scope.hasPermission('zemauth.can_include_model_ids_in_reports')) {
            data.include_model_ids = $scope.export.includeIds;
        }

        if ($scope.hasPermission('zemauth.can_include_totals_in_reports')) {
            data.include_totals = $scope.export.includeTotals;
        }

        api.scheduledReports.addScheduledReport(url, data).then(
            function (data) {
                $scope.$close();
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
        $scope.export.dayOfWeek = $scope.exportSchedulingDayOfWeek[1];
        $scope.export.type = $scope.defaultOption;
        $scope.export.timePeriod = $scope.exportSchedulingTimePeriods[0];
        $scope.timePeriodChanged();
        $scope.frequencyChanged();
    };
    $scope.init();
});
