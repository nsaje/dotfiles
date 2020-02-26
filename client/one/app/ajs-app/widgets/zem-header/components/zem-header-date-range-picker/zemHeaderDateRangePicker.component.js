var routerHelpers = require('../../../../../shared/helpers/router.helpers');

angular.module('one.widgets').component('zemHeaderDateRangePicker', {
    template: require('./zemHeaderDateRangePicker.component.html'), // eslint-disable-line max-len
    controller: function(
        NgRouter,
        $timeout,
        config,
        zemDataFilterService,
        zemHeaderDateRangePickerService
    ) {
        // eslint-disable-line max-len
        var $ctrl = this;
        $ctrl.config = config;
        $ctrl.isInitialized = false;

        var dateRangeUpdateHandler;

        $ctrl.$onInit = function() {
            var predefinedRanges = zemHeaderDateRangePickerService.getPredefinedRanges();

            $ctrl.dateRangePickerOptions = {
                alwaysShowCalendars: true,
                minDate: moment('2016-02-01'),
                maxDate: moment().endOf('month'),
                ranges: predefinedRanges,
                opens: 'left',
                applyClass:
                    'button button--highlight button--with-icon check-icon',
                cancelClass: 'button',
                linkedCalendars: false,
                locale: {
                    format: 'MMM D, YYYY',
                },
                eventHandlers: {
                    'apply.daterangepicker': handleDateRangeUpdateFromPicker,
                    // Add/remove open class from date range picker dropdown menu in order to apply opening animation
                    'show.daterangepicker': function() {
                        angular.element('.date-range-picker-input').blur();
                        angular
                            .element('.date-range-picker-input')
                            .css('cursor', 'text');
                        angular
                            .element('.daterangepicker.dropdown-menu')
                            .addClass('open');
                    },
                    'hide.daterangepicker': function() {
                        angular
                            .element('.date-range-picker-input')
                            .css('cursor', 'pointer');
                        angular
                            .element('.daterangepicker.dropdown-menu')
                            .removeClass('open');
                    },
                },
            };

            $timeout(function() {
                // Workaround to add a class used for styling to date range picker dropdown after DOM was rendered
                angular
                    .element('.daterangepicker.dropdown-menu')
                    .addClass('zem-header-date-range-picker-dropdown');
            }, 0);

            dateRangeUpdateHandler = zemDataFilterService.onDateRangeUpdate(
                updateInternalState
            );

            initFromUrlParams();
        };

        $ctrl.$onDestroy = function() {
            if (dateRangeUpdateHandler) dateRangeUpdateHandler();
        };

        function initFromUrlParams() {
            var activatedRoute = routerHelpers.getActivatedRoute(NgRouter);
            var queryParams = activatedRoute.snapshot.queryParams;

            // Date range
            var dateRange = {
                startDate: moment().startOf('month'),
                endDate: moment().endOf('month'),
            };
            var startDateParam = queryParams.start_date;
            var endDateParam = queryParams.end_date;
            if (startDateParam) dateRange.startDate = moment(startDateParam);
            if (endDateParam) dateRange.endDate = moment(endDateParam);

            zemDataFilterService.setDateRange(dateRange);
        }

        function handleDateRangeUpdateFromPicker() {
            zemDataFilterService.setDateRange($ctrl.dateRange);
        }

        function updateInternalState() {
            $ctrl.dateRange = zemDataFilterService.getDateRange();
            $ctrl.isInitialized = true;
        }
    },
});

//
// [PATCH] Bootstrap DateRangePicker
//         Enable independent date selection - start date on left calendar and end date on the right
//
angular.element(document).ready(function() {
    window.daterangepicker.prototype.clickDate = function(e) {
        if (!$(e.target).hasClass('available')) return;

        var title = $(e.target).attr('data-title');
        var row = title.substr(1, 1);
        var col = title.substr(3, 1);
        var cal = $(e.target).parents('.calendar');

        var isLeftCalendar = cal.hasClass('left');
        var date = isLeftCalendar
            ? this.leftCalendar.calendar[row][col]
            : this.rightCalendar.calendar[row][col];

        if (isLeftCalendar) {
            this.setStartDate(date);
            if (date.isAfter(this.endDate, 'day')) {
                this.setEndDate(date);
            }
        } else {
            if (date.isBefore(this.startDate, 'day')) {
                this.setStartDate(date);
            }
            this.setEndDate(date);
        }

        this.updateView();
        e.stopPropagation();
    };

    window.daterangepicker.prototype.updateMonthsInView = function() {
        this.leftCalendar.month = this.startDate.clone().date(1);
        if (this.endDate) {
            this.rightCalendar.month = this.endDate.clone().date(1);
        } else {
            this.rightCalendar.month = this.startDate.clone().date(1);
        }
    };
});
