angular.module('one.widgets').component('zemHeaderMenu', {
    template: require('./zemHeaderMenu.component.html'),
    controller: function(
        config,
        zemHeaderMenuService,
        zemNavigationNewService,
        zemAuthStore
    ) {
        var activeEntityUpdateHandler;

        var $ctrl = this;
        $ctrl.config = config;
        $ctrl.menuStructure = {};
        $ctrl.executeAction = executeAction;

        $ctrl.$onInit = function() {
            setUserInfo();
            activeEntityUpdateHandler = zemNavigationNewService.onActiveEntityChange(
                refreshMenu
            );
        };

        $ctrl.$onDestroy = function() {
            if (activeEntityUpdateHandler) activeEntityUpdateHandler();
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
