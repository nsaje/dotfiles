angular.module('one.common').component('zemHeaderMenu', {
    template: require('./zemHeaderMenu.component.html'),
    controller: function(config, zemHeaderMenuService, zemUserService) {
        var $ctrl = this;
        $ctrl.config = config;
        $ctrl.getActions = zemHeaderMenuService.getAvailableActions;
        $ctrl.execute = execute;

        var currentUserUpdateHandler;

        $ctrl.$onInit = function() {
            setUserInfo();

            currentUserUpdateHandler = zemUserService.onCurrentUserUpdated(
                setUserInfo
            );
        };

        $ctrl.$onDestroy = function() {
            if (currentUserUpdateHandler) currentUserUpdateHandler();
        };

        function setUserInfo() {
            var user = zemUserService.current();
            $ctrl.userName = user ? user.name : null;
            $ctrl.userEmail = user ? user.email : null;
        }

        function execute(action) {
            action.callback(action.params);
        }
    },
});
