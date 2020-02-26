require('./zemHeader.component.less');

var RoutePathName = require('../../../app.constants').RoutePathName;

angular.module('one.widgets').component('zemHeader', {
    template: require('./zemHeader.component.html'),
    controller: function(
        $rootScope,
        NgRouter,
        config,
        zemNavigationNewService
    ) {
        var $ctrl = this;
        var zemNavigationEndHandler;

        $ctrl.config = config;
        $ctrl.navigateTo = navigateTo;

        $ctrl.$onInit = function() {
            updateComponentState();

            $ctrl.homeHref = zemNavigationNewService.getHomeHref();
            zemNavigationEndHandler = $rootScope.$on(
                '$zemNavigationEnd',
                updateComponentState
            );
        };

        $ctrl.$onDestroy = function() {
            if (zemNavigationEndHandler) {
                zemNavigationEndHandler();
            }
        };

        function updateComponentState() {
            $ctrl.homeHref = zemNavigationNewService.getHomeHref();
            $ctrl.isDateRangePickerVisible = false;
            $ctrl.isFilterSelectorToggleVisible = false;

            if (
                NgRouter.url.includes(
                    RoutePathName.APP_BASE + '/' + RoutePathName.ANALYTICS
                )
            ) {
                $ctrl.isDateRangePickerVisible = true;
                $ctrl.isFilterSelectorToggleVisible = true;
            }

            if (
                NgRouter.url.includes(
                    RoutePathName.APP_BASE + '/' + RoutePathName.PIXELS_LIBRARY
                )
            ) {
                $ctrl.isFilterSelectorToggleVisible = true;
            }
        }

        function navigateTo($event) {
            $event.stopPropagation();
            $event.preventDefault();
            NgRouter.navigateByUrl($ctrl.homeHref);
        }
    },
});
