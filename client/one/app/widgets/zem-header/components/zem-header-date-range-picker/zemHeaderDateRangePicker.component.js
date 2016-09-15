angular.module('one.widgets').component('zemHeaderDateRangePicker', {
    templateUrl: '/app/widgets/zem-header/components/zem-header-date-range-picker/zemHeaderDateRangePicker.component.html', // eslint-disable-line max-len
    controller: ['$state', 'config', 'zemDataFilterService', 'zemHeaderDateRangePickerService', function ($state, config, zemDataFilterService, zemHeaderDateRangePickerService) { // eslint-disable-line max-len
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
                },
            };

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
