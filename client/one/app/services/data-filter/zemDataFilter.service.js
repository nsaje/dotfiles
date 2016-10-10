angular.module('one.services').service('zemDataFilterService', ['$rootScope', '$location', 'zemPubSubService', function ($rootScope, $location, zemPubSubService) { // eslint-disable-line max-len
    this.init = init;
    this.getDateRange = getDateRange;
    this.setDateRange = setDateRange;
    this.onDateRangeUpdate = onDateRangeUpdate;

    var EVENTS = {
        ON_DATE_RANGE_UPDATE: 'zem-data-filter-service-on-date-range-update',
    };

    var dateRange = {startDate: null, endDate: null};

    function init () {
        dateRange = {
            startDate: moment().subtract(29, 'day').hours(0).minutes(0).seconds(0).milliseconds(0),
            endDate: moment().subtract(1, 'day').endOf('day'),
        };

        initFilterFromUrlParams();
    }

    function initFilterFromUrlParams () {
        var startDate = $location.search().start_date;
        var endDate = $location.search().end_date;

        if (startDate) {
            dateRange.startDate = moment(startDate);
        }

        if (endDate) {
            dateRange.endDate = moment(endDate);
        }
    }

    function getDateRange () {
        return angular.copy(dateRange);
    }

    function setDateRange (newDateRange) {
        var updated = false;

        if (newDateRange.startDate.isValid() && !newDateRange.startDate.isSame(dateRange.startDate)) {
            dateRange.startDate = newDateRange.startDate;
            updated = true;
        }

        if (newDateRange.endDate.isValid() && !newDateRange.endDate.isSame(dateRange.endDate)) {
            dateRange.endDate = newDateRange.endDate;
            updated = true;
        }

        if (updated) {
            pubSub.notify(EVENTS.ON_DATE_RANGE_UPDATE, getDateRange());

            $location.search(
                'start_date',
                dateRange.startDate ? dateRange.startDate.format('YYYY-MM-DD') : null
            );
            $location.search(
                'end_date',
                dateRange.endDate ? dateRange.endDate.format('YYYY-MM-DD') : null
            );
        }
    }

    //
    // Listener functionality
    //
    var pubSub = zemPubSubService.createInstance();
    function onDateRangeUpdate (callback) {
        return pubSub.register(EVENTS.ON_DATE_RANGE_UPDATE, callback);
    }
}]);
