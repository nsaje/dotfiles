angular.module('one.widgets').component('zemHeaderDateRangePicker', {
    bindings: {
        dateRange: '=',
        dateRangePickerOptions: '=',
    },
    templateUrl: '/app/widgets/zem-header/components/zem-header-date-range-picker/zemHeaderDateRangePicker.component.html', // eslint-disable-line max-len
    controller: ['$state', 'config', function ($state, config) {
        var $ctrl = this;
        $ctrl.config = config;
        $ctrl.isVisible = isVisible;

        function isVisible () {
            return !(
                $state.includes('*.*.agency')
                || $state.includes('*.*.settings')
                || $state.includes('*.*.budget')
                || $state.includes('*.*.budget')
            );
        }
    }],
});
