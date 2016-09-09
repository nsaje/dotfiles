angular.module('one.widgets').component('zemHeaderMenu', {
    templateUrl: '/app/widgets/zem-header/components/zem-header-menu/zemHeaderMenu.component.html',
    controller: ['zemHeaderMenuService', 'zemUserService', function (zemHeaderMenuService, zemUserService) {
        var $ctrl = this;
        $ctrl.getActions = zemHeaderMenuService.getAvailableActions;
        $ctrl.execute = execute;

        $ctrl.$onInit = function () {
            $ctrl.userEmail = zemUserService.getUserEmail();
        };

        function execute (action) {
            action.callback(action.params);
        }
    }],
});
