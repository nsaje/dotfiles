angular.module('one.widgets').component('zemReportSchedule', {
    bindings: {
        close: '&',
        resolve: '<',
    },
    template: require('./zemReportSchedule.component.html'),
    controller: function(
        $interval,
        zemReportService,
        zemUserService,
        zemReportScheduleService
    ) {
        // eslint-disable-line max-len
        var $ctrl = this;

        // Public API
        $ctrl.dayOfWeekShown = dayOfWeekShown;
        $ctrl.scheduleReport = scheduleReport;

        // template variables
        $ctrl.optionsFrequencies = zemReportScheduleService.FREQUENCIES;
        $ctrl.optionsTimePeriods = zemReportScheduleService.TIME_PERIODS;
        $ctrl.optionsDaysOfWeek = zemReportScheduleService.DAYS_OF_WEEK;

        $ctrl.name = '';

        $ctrl.frequency = zemReportScheduleService.FREQUENCIES[0];
        $ctrl.timePeriod = zemReportScheduleService.TIME_PERIODS[0];
        $ctrl.dayOfWeek = zemReportScheduleService.DAYS_OF_WEEK[1];

        $ctrl.recipients = '';
        $ctrl.user = undefined;
        $ctrl.queryConfig = {};

        $ctrl.jobPosted = false;

        $ctrl.$onInit = function() {
            $ctrl.user = zemUserService.current();
        };

        function dayOfWeekShown() {
            return $ctrl.frequency.value === 'WEEKLY';
        }

        function scheduleReport() {
            $ctrl.jobPosted = true;
            $ctrl.errors = undefined;
            zemReportService
                .scheduleReport(
                    $ctrl.resolve.api,
                    $ctrl.queryConfig,
                    getRecipientsList(),
                    $ctrl.name,
                    $ctrl.frequency.value,
                    $ctrl.timePeriod.value,
                    $ctrl.dayOfWeek.value
                )
                .then($ctrl.close)
                .catch(function(data) {
                    $ctrl.jobPosted = false;
                    $ctrl.hasError = true;
                    $ctrl.errors = data.data.errors;
                });
        }

        function getRecipientsList() {
            var recipients = [];
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
