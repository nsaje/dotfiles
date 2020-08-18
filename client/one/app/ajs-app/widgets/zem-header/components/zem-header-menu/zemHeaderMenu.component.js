angular.module('one.widgets').component('zemHeaderMenu', {
    template: require('./zemHeaderMenu.component.html'),
    controller: function(config, zemHeaderMenuService, zemAuthStore) {
        var $ctrl = this;
        $ctrl.config = config;
        $ctrl.getActions = zemHeaderMenuService.getAvailableActions;
        $ctrl.execute = execute;

        $ctrl.$onInit = function() {
            setUserInfo();
        };

        function setUserInfo() {
            var user = zemAuthStore.getCurrentUser();
            $ctrl.userName = user ? user.name : null;
            $ctrl.userEmail = user ? user.email : null;
        }

        function execute(action) {
            action.callback(action.params);
        }
    },
});
