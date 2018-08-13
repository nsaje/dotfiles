angular.module('one.widgets').service('zemReportScheduleService', function() {
    // eslint-disable-line max-len

    var FREQUENCIES = [
        {
            name: 'Daily',
            value: 'DAILY',
        },
        {
            name: 'Weekly',
            value: 'WEEKLY',
        },
        {
            name: 'Monthly (1st)',
            value: 'MONTHLY',
        },
    ];

    var DAYS_OF_WEEK = [
        {
            name: 'Sunday',
            value: 'SUNDAY',
        },
        {
            name: 'Monday',
            value: 'MONDAY',
        },
        {
            name: 'Tuesday',
            value: 'TUESDAY',
        },
        {
            name: 'Wednesday',
            value: 'WEDNESDAY',
        },
        {
            name: 'Thursday',
            value: 'THURSDAY',
        },
        {
            name: 'Friday',
            value: 'FRIDAY',
        },
        {
            name: 'Saturday',
            value: 'SATURDAY',
        },
    ];

    var TIME_PERIODS = [
        {
            name: 'Yesterday',
            value: 'YESTERDAY',
        },
        {
            name: 'Last 7 Days',
            value: 'LAST_7_DAYS',
        },
        {
            name: 'Last 30 Days',
            value: 'LAST_30_DAYS',
        },
        {
            name: 'This Week',
            value: 'THIS_WEEK',
        },
        {
            name: 'Last Week',
            value: 'LAST_WEEK',
        },
        {
            name: 'This Month',
            value: 'THIS_MONTH',
        },
        {
            name: 'Last Month',
            value: 'LAST_MONTH',
        },
    ];

    // Public API
    this.FREQUENCIES = FREQUENCIES;
    this.DAYS_OF_WEEK = DAYS_OF_WEEK;
    this.TIME_PERIODS = TIME_PERIODS;
    this.MAPPING_FREQUENCIES = getMapping(FREQUENCIES);
    this.MAPPING_DAYS_OF_WEEK = getMapping(DAYS_OF_WEEK);
    this.MAPPING_TIME_PERIODS = getMapping(TIME_PERIODS);

    function getMapping(options) {
        var mapping = {};
        options.forEach(function(option) {
            mapping[option.value] = option.name;
        });
        return mapping;
    }
});
