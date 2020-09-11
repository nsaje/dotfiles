//
// TODO: On major update, refactor to component
//
angular
    .module('one.widgets')
    .controller('zemAddScheduledReportModalCtrl', function(
        $scope,
        $q,
        $http,
        zemAddScheduledReportModalEndpoint,
        zemDataFilterService
    ) {
        // eslint-disable-line max-len
        $scope.exportSchedulingFrequencies = options.exportFrequency;
        $scope.exportSchedulingTimePeriods = options.exportTimePeriod;
        $scope.exportSchedulingDayOfWeek = options.exportDayOfWeek;
        $scope.showInProgress = false;
        $scope.hasError = false;
        $scope.breakdownByDayDisabled = false;
        $scope.dayOfWeekShown = false;

        $scope.export = {};
        $scope.validationErrors = {};

        $scope.timePeriodChanged = function() {
            $scope.breakdownByDayDisabled = false;
            if (
                $scope.export.timePeriod.value ===
                constants.exportTimePeriod.YESTERDAY
            ) {
                $scope.breakdownByDayDisabled = true;
                $scope.export.byDay = false;
            }
        };

        $scope.frequencyChanged = function() {
            $scope.dayOfWeekShown = false;
            if (
                $scope.export.frequency.value ===
                constants.exportFrequency.WEEKLY
            ) {
                $scope.dayOfWeekShown = true;
            }

            if (
                !$scope.hasPermission(
                    'zemauth.can_set_time_period_in_scheduled_reports'
                )
            ) {
                $scope.breakdownByDayDisabled = false;
                if (
                    $scope.export.frequency.value ===
                    constants.exportFrequency.DAILY
                ) {
                    $scope.breakdownByDayDisabled = true;
                    $scope.export.byDay = false;
                }
            }
        };

        $scope.addScheduledReport = function() {
            $scope.clearErrors();
            $scope.showInProgress = true;
            var url = $scope.baseUrl + 'export/';
            var dateRange = zemDataFilterService.getDateRange();
            var filteredSources = zemDataFilterService
                .getFilteredSources()
                .join(',');

            var data = {
                type: $scope.export.type.value,
                start_date: dateRange.startDate.format(),
                end_date: dateRange.endDate.format(),
                order: $scope.order,
                by_day: $scope.export.byDay,
                additional_fields: $scope.getAdditionalColumns().join(','),
                filtered_sources: filteredSources,
                frequency: $scope.export.frequency.value,
                day_of_week: $scope.export.dayOfWeek.value,
                time_period: $scope.export.timePeriod.value,
                recipient_emails: $scope.export.recipientEmails,
                report_name: $scope.export.reportName,
            };

            var filteredAgencies = zemDataFilterService.getFilteredAgencies();
            if (filteredAgencies.length > 0) {
                data.filtered_agencies = filteredAgencies.join(',');
            }

            var filteredAccountTypes = zemDataFilterService.getFilteredAccountTypes();
            if (filteredAccountTypes.length > 0) {
                data.filtered_account_types = filteredAccountTypes.join(',');
            }

            data.include_model_ids = $scope.export.includeIds;
            data.include_totals = $scope.export.includeTotals;

            zemAddScheduledReportModalEndpoint
                .put(url, data)
                .then(
                    function() {
                        $scope.$close();
                    },
                    function(errors) {
                        if (errors) {
                            $scope.validationErrors = errors;
                        } else {
                            $scope.hasError = true;
                        }
                    }
                )
                .finally(function() {
                    $scope.showInProgress = false;
                });
        };

        $scope.clearErrors = function() {
            $scope.hasError = false;
            $scope.validationErrors = {};
        };

        $scope.init = function() {
            $scope.export.frequency = $scope.exportSchedulingFrequencies[0];
            $scope.export.dayOfWeek = $scope.exportSchedulingDayOfWeek[1];
            $scope.export.type = $scope.defaultOption;
            $scope.export.timePeriod = $scope.exportSchedulingTimePeriods[0];
            $scope.timePeriodChanged();
            $scope.frequencyChanged();
        };
        $scope.init();
    });

angular
    .module('one.widgets')
    .service('zemAddScheduledReportModalEndpoint', function($q, $http) {
        this.put = put;

        function put(url, data) {
            var deferred = $q.defer();
            $http
                .put(url, data)
                .success(function(data, status) {
                    if (parseInt(status) !== 200) {
                        deferred.reject(data);
                    }
                    deferred.resolve();
                })
                .error(function(data) {
                    var errors = null;
                    if (data && data.data && data.data.errors) {
                        errors = data.data.errors;
                    }
                    return deferred.reject(errors);
                });

            return deferred.promise;
        }
    });
