angular.module('one.widgets').component('zemHeaderMenu', {
    templateUrl: '/app/widgets/zem-header/components/zem-header-menu/zemHeaderMenu.component.html',
    controller: ['zemHeaderMenuService', 'userService', function (zemHeaderMenuService, userService) {
        var $ctrl = this;
        $ctrl.execute = execute;

        $ctrl.$onInit = function () {
            $ctrl.userEmail = userService.getEmail();
            updateAvailableActions();
        };

        function updateAvailableActions () {
            $ctrl.actions = zemHeaderMenuService.getAvailableActions();
        }

        function execute (action) {
            action.callback(action.params);
            updateAvailableActions();
        }
    }],
});
