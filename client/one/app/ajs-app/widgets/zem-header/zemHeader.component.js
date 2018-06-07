require('./zemHeader.component.less');

angular.module('one.widgets').component('zemHeader', {
    template: require('./zemHeader.component.html'),
    controller: function ($rootScope, $state, $window, config, NgZone) {
        var $ctrl = this;
        var zemStateChangeHandler;

        $ctrl.config = config;

        $ctrl.$onInit = function () {
            updateComponentsVisibility();

            NgZone.runOutsideAngular(function () {
                angular.element($window).on('scroll', handleScroll);
            });

            zemStateChangeHandler = $rootScope.$on('$zemStateChangeSuccess', updateComponentsVisibility);
        };

        $ctrl.$onDestroy = function () {
            angular.element($window).off('scroll', handleScroll);

            if (zemStateChangeHandler) {
                zemStateChangeHandler();
            }
        };

        function updateComponentsVisibility () {
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

        var isHeaderFixed = false;
        function handleScroll (event) {
            NgZone.runOutsideAngular(function () {
                var st = $(event.target).scrollTop();
                if (!isHeaderFixed && st > 50) {
                    isHeaderFixed = true;
                    $('body').addClass('fixed-header');
                } else if (isHeaderFixed && st <= 50) {
                    isHeaderFixed = false;
                    $('body').removeClass('fixed-header');
                }
            });
        }
    },
});
