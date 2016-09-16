angular.module('one.widgets').component('zemHeaderMenu', {
    templateUrl: '/app/widgets/zem-header/components/zem-header-menu/zemHeaderMenu.component.html',
    controller: ['config', 'zemHeaderMenuService', 'zemUserService', function (config, zemHeaderMenuService, zemUserService) { // eslint-disable-line max-len
        var $ctrl = this;
        $ctrl.config = config;
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
