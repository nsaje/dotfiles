angular.module('one.common').component('zemHeaderDateRangePicker', {
    template: require('./zemHeaderDateRangePicker.component.html'), // eslint-disable-line max-len
    controller: function(
        $state,
        $timeout,
        config,
        zemDataFilterService,
        zemHeaderDateRangePickerService
    ) {
        // eslint-disable-line max-len
        var $ctrl = this;
        $ctrl.config = config;
        $ctrl.isVisible = isVisible;

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

            $ctrl.dateRange = zemDataFilterService.getDateRange();

            dateRangeUpdateHandler = zemDataFilterService.onDateRangeUpdate(
                onDateRangeDataFilterUpdate
            );
        };

        $ctrl.$onDestroy = function() {
            if (dateRangeUpdateHandler) dateRangeUpdateHandler();
        };

        function isVisible() {
            return !(
                $state.includes('*.*.agency') ||
                $state.includes('*.*.settings') ||
                $state.includes('*.*.budget') ||
                $state.includes('*.*.budget')
            );
        }

        function handleDateRangeUpdateFromPicker() {
            zemDataFilterService.setDateRange($ctrl.dateRange);
        }

        function onDateRangeDataFilterUpdate(event, updatedDateRange) {
            $ctrl.dateRange = updatedDateRange;
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
