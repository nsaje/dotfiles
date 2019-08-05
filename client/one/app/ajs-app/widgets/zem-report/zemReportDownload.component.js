angular.module('one.widgets').component('zemReportDownload', {
    bindings: {
        close: '&',
        resolve: '<',
    },
    template: require('./zemReportDownload.component.html'),
    controller: function(
        $interval,
        zemReportService,
        zemPermissions,
        zemUserService,
        zemDataFilterService
    ) {
        // eslint-disable-line max-len
        var $ctrl = this;

        // Public API
        $ctrl.startReport = startReport;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;
        $ctrl.cancel = cancel;

        // template variables
        $ctrl.sendReport = false;
        $ctrl.recipients = '';
        $ctrl.user = undefined;
        $ctrl.queryConfig = {};

        $ctrl.jobPosted = false;
        $ctrl.jobDone = false;
        $ctrl.reportSent = false;
        $ctrl.pollInterval = null;

        $ctrl.$onInit = function() {
            $ctrl.user = zemUserService.current();
            $ctrl.dateRange = zemDataFilterService.getDateRange();
        };

        function cancel() {
            stopPolling();
            $ctrl.close();
        }

        function startPolling(id) {
            if ($ctrl.pollInterval !== null) {
                return;
            }

            $ctrl.pollInterval = $interval(function() {
                zemReportService
                    .getReport(id)
                    .then(function(data) {
                        if (data.data.status === 'IN_PROGRESS') {
                            return;
                        }

                        if (data.data.status === 'FAILED') {
                            $ctrl.jobDone = true;
                            $ctrl.hasError = true;
                            $ctrl.errorMsg = data.data.result;
                        } else if (data.data.status === 'DONE') {
                            $ctrl.jobDone = true;
                            $ctrl.reportUrl = data.data.result;
                        }
                        stopPolling();
                    })
                    .catch(function(data) {
                        $ctrl.jobDone = true;
                        $ctrl.hasError = true;
                        $ctrl.reportJobID = id;
                        if (data) {
                            $ctrl.errors = data.data;
                        }
                        stopPolling();
                    });
            }, 2500);
        }

        function stopPolling() {
            if ($ctrl.pollInterval !== null) {
                $interval.cancel($ctrl.pollInterval);
                $ctrl.pollInterval = null;
            }
        }

        function startReport() {
            $ctrl.jobPosted = true;
            $ctrl.errors = undefined;
            $ctrl.errorMsg = undefined;
            zemReportService
                .startReport(
                    $ctrl.resolve.api,
                    $ctrl.queryConfig,
                    getRecipientsList()
                )
                .then(function(data) {
                    if ($ctrl.sendReport) {
                        $ctrl.jobDone = true;
                        $ctrl.reportSent = true;
                    } else {
                        startPolling(data.data.id);
                    }
                })
                .catch(function(data) {
                    $ctrl.jobDone = true;
                    $ctrl.hasError = true;
                    $ctrl.errors = data.details;
                    if ($ctrl.errors) {
                        $ctrl.jobPosted = false;
                        $ctrl.jobDone = false;
                    }
                });
        }

        function getRecipientsList() {
            if (!$ctrl.sendReport) {
                return [];
            }
            var recipients = [$ctrl.user.email];
            var list = $ctrl.recipients.split(',');
            for (var i = 0; i < list.length; i++) {
                if (list[i] && list[i].trim()) {
                    recipients.push(list[i]);
                }
            }
            return recipients;
        }
    },
});
