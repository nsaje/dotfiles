angular.module('one.widgets').component('zemHeaderMenu', {
    template: require('./zemHeaderMenu.component.html'),
    controller: function(
        config,
        $rootScope,
        zemHeaderMenuService,
        zemNavigationNewService,
        zemAuthStore,
        zemDataFilterService
    ) {
        var activeEntityUpdateHandler;
        var agencyFilterUpdateHandler;
        var zemNavigationEndHandler;

        var $ctrl = this;
        $ctrl.config = config;
        $ctrl.menuStructure = {};
        $ctrl.executeAction = executeAction;

        $ctrl.$onInit = function() {
            setUserInfo();
            activeEntityUpdateHandler = zemNavigationNewService.onActiveEntityChange(
                refreshMenu
            );
            agencyFilterUpdateHandler = zemDataFilterService.onFilteredAgenciesUpdate(
                refreshMenu
            );
            zemNavigationEndHandler = $rootScope.$on(
                '$zemNavigationEnd',
                refreshMenu
            );
        };

        $ctrl.$onDestroy = function() {
            if (activeEntityUpdateHandler) activeEntityUpdateHandler();
            if (agencyFilterUpdateHandler) agencyFilterUpdateHandler();
            if (zemNavigationEndHandler) zemNavigationEndHandler();
        };

        function setUserInfo() {
            var user = zemAuthStore.getCurrentUser();
            $ctrl.userName = user ? user.name : null;
            $ctrl.userEmail = user ? user.email : null;
        }

        function executeAction(action, $event) {
            if (action.callback) {
                $event.preventDefault();
                action.callback(action.params);
            }
        }

        function refreshMenu() {
            $ctrl.menuStructure = zemHeaderMenuService.getMenuStructure();
        }
    },
});
