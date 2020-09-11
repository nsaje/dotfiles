angular
    .module('one.widgets')
    .service('zemScheduledReportsStateService', function(
        zemScheduledReportsEndpoint,
        $q,
        $timeout,
        zemAuthStore,
        zemReportScheduleService
    ) {
        // eslint-disable-line max-len
        this.createInstance = createInstance;

        function createInstance(account) {
            return new zemScheduledReportsStateService(account);
        }

        function zemScheduledReportsStateService(account) {
            var self = this;
            this.getState = getState;
            this.reloadReports = reloadReports;
            this.removeReport = removeReport;

            var state = {};

            function getState() {
                return state;
            }

            function reloadReports() {
                if (account === undefined) return $q.reject();

                delete state.reports;
                delete state.loadErrorMessage;
                state.loadReportsRequestInProgress = true;

                return zemScheduledReportsEndpoint
                    .list(account)
                    .then(function(data) {
                        data = formatReports(data);
                        state.reports = data;
                    })
                    .catch(function() {
                        state.loadErrorMessage = 'Error retrieving reports';
                        return $q.reject();
                    })
                    .finally(function() {
                        state.loadReportsRequestInProgress = false;
                    });
            }

            var hideMessageTimeout;
            function removeReport(report) {
                var id = report.scheduledReportId || report.id;
                if (!id) return $q.reject();

                delete state.removeErrorMessage;
                state.removeRequestInProgress = true;

                if (hideMessageTimeout) {
                    $timeout.cancel(hideMessageTimeout);
                }

                return (
                    zemScheduledReportsEndpoint
                        .remove(id)
                        // Calling self.reloadReports instead of reloadReports in order to be able to set a spy in tests on
                        // reloadReports method for specific instance of zemScheduledReportsStateService
                        .then(self.reloadReports)
                        .catch(function() {
                            state.removeErrorMessage =
                                'Error removing report. Please contact support.';
                            hideMessageTimeout = $timeout(function() {
                                delete state.removeErrorMessage;
                            }, 3000);
                            return $q.reject();
                        })
                        .finally(function() {
                            state.removeRequestInProgress = false;
                        })
                );
            }
        }

        function formatReports(reports) {
            return reports.map(function(report) {
                var dayOfWeek = '';
                if (report.frequency === 'WEEKLY') {
                    dayOfWeek =
                        zemReportScheduleService.MAPPING_DAYS_OF_WEEK[
                            report.dayOfWeek
                        ];
                }
                return {
                    id: report.id,
                    name: report.name,
                    user: report.user,
                    breakdown: report.breakdown.join(', '),
                    level: report.level,
                    dayOfWeek: dayOfWeek,
                    frequency:
                        zemReportScheduleService.MAPPING_FREQUENCIES[
                            report.frequency
                        ],
                    timePeriod:
                        zemReportScheduleService.MAPPING_TIME_PERIODS[
                            report.timePeriod
                        ],
                    recipients: report.recipients.join(', '),
                };
            });
        }
    });
