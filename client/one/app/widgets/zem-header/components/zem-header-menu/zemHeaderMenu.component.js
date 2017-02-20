angular.module('one.widgets').component('zemHeaderMenu', {
    templateUrl: '/app/widgets/zem-header/components/zem-header-menu/zemHeaderMenu.component.html',
    controller: function (config, zemHeaderMenuService, zemUserService) {
        var $ctrl = this;
        $ctrl.config = config;
        $ctrl.getActions = zemHeaderMenuService.getAvailableActions;
        $ctrl.execute = execute;

        $ctrl.$onInit = function () {
            $ctrl.userEmail = zemUserService.current().email;
        };

        function execute (action) {
            action.callback(action.params);
        }
    },
});
