require('./zemAccessPermissions.component.less');

angular.module('one.widgets').component('zemAccessPermissions', {
    bindings: {
        account: '<',
    },
    template: require('./zemAccessPermissions.component.html'),
    controller: function(zemPermissions, zemAccessPermissionsStateService) {
        // eslint-disable-line max-len
        var $ctrl = this;

        $ctrl.createUserData = {};

        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.create = create;

        $ctrl.$onInit = function() {
            $ctrl.stateService = zemAccessPermissionsStateService.getInstance(
                $ctrl.account
            );
            $ctrl.stateService.initialize();
            $ctrl.state = $ctrl.stateService.getState();

            $ctrl.remove = $ctrl.stateService.remove;
            $ctrl.activate = $ctrl.stateService.activate;
            $ctrl.undo = $ctrl.stateService.undo;
            $ctrl.promote = $ctrl.stateService.promote;
            $ctrl.downgrade = $ctrl.stateService.downgrade;
            $ctrl.enableApi = $ctrl.stateService.enableApi;
            $ctrl.showCollapsed = false;
        };

        function create() {
            $ctrl.stateService.create($ctrl.createUserData).then(function() {
                $ctrl.createUserData = {};
            });
        }
    },
});
