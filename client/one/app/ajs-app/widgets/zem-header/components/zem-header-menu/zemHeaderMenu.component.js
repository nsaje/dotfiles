angular.module('one.widgets').component('zemHeaderMenu', {
    template: require('./zemHeaderMenu.component.html'),
    controller: function (config, zemHeaderMenuService, zemUserService) {
        var $ctrl = this;
        $ctrl.config = config;
        $ctrl.getActions = zemHeaderMenuService.getAvailableActions;
        $ctrl.execute = execute;

        var currentUserUpdateHandler;

        $ctrl.$onInit = function () {
            setUserEmail();

            currentUserUpdateHandler = zemUserService.onCurrentUserUpdated(setUserEmail);
        };

        $ctrl.$onDestroy = function () {
            if (currentUserUpdateHandler) currentUserUpdateHandler();
        };

        function setUserEmail () {
            var user = zemUserService.current();
            $ctrl.userEmail = user ? user.email : null;
        }

        function execute (action) {
            action.callback(action.params);
        }
    },
});
