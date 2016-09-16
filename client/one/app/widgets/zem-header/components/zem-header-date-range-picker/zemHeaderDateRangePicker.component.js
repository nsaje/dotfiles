angular.module('one.widgets').component('zemHeaderDateRangePicker', {
    templateUrl: '/app/widgets/zem-header/components/zem-header-date-range-picker/zemHeaderDateRangePicker.component.html', // eslint-disable-line max-len
    controller: ['$state', '$timeout', 'config', 'zemDataFilterService', 'zemHeaderDateRangePickerService', function ($state, $timeout, config, zemDataFilterService, zemHeaderDateRangePickerService) { // eslint-disable-line max-len
        var $ctrl = this;
        $ctrl.config = config;
        $ctrl.isVisible = isVisible;

        $ctrl.$onInit = function () {
            var predefinedRanges = zemHeaderDateRangePickerService.getPredefinedRanges();
            $ctrl.dateRangePickerOptions = {
                maxDate: moment().endOf('month'),
                ranges: predefinedRanges,
                opens: 'left',
                applyClass: 'btn-primary',
                eventHandlers: {
                    'apply.daterangepicker': handleDateRangeUpdateFromPicker,
                    // Add/remove open class from date range picker dropdown menu in order to apply opening animation
                    'show.daterangepicker': function () {
                        angular.element('.daterangepicker.dropdown-menu').addClass('open');
                    },
                    'hide.daterangepicker': function () {
                        angular.element('.daterangepicker.dropdown-menu').removeClass('open');
                    },
                },
            };

            $timeout(function () {
                // Workaround to add a class used for styling to date range picker dropdown after DOM was rendered
                angular.element('.daterangepicker.dropdown-menu').addClass('zem-header-date-range-picker-dropdown');
            }, 0);

            $ctrl.dateRange = zemDataFilterService.getDateRange();

            zemDataFilterService.onDateRangeUpdate(onDateRangeDataFilterUpdate);
        };

        function isVisible () {
            return !(
                $state.includes('*.*.agency')
                || $state.includes('*.*.settings')
                || $state.includes('*.*.budget')
                || $state.includes('*.*.budget')
            );
        }

        function handleDateRangeUpdateFromPicker () {
            zemDataFilterService.setDateRange($ctrl.dateRange);
        }

        function onDateRangeDataFilterUpdate (event, updatedDateRange) {
            $ctrl.dateRange = updatedDateRange;
        }
    }],
});
