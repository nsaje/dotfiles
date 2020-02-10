require('./zemHeader.component.less');

angular.module('one.widgets').component('zemHeader', {
    template: require('./zemHeader.component.html'),
    controller: function($rootScope, $state, $window, config) {
        var $ctrl = this;
        var zemStateChangeHandler;

        $ctrl.config = config;

        $ctrl.$onInit = function() {
            updateComponentsVisibility();

            zemStateChangeHandler = $rootScope.$on(
                '$zemStateChangeSuccess',
                updateComponentsVisibility
            );
        };

        $ctrl.$onDestroy = function() {
            if (zemStateChangeHandler) {
                zemStateChangeHandler();
            }
        };

        function updateComponentsVisibility() {
            $ctrl.isDateRangePickerVisible = false;
            $ctrl.isFilterSelectorToggleVisible = false;

            if ($state.includes('v2.analytics')) {
                $ctrl.isDateRangePickerVisible = true;
                $ctrl.isFilterSelectorToggleVisible = true;
            }

            if ($state.includes('v2.pixels')) {
                $ctrl.isFilterSelectorToggleVisible = true;
            }
        }
    },
});
