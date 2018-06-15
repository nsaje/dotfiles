require('./zemAccessPermissions.component.less');

angular.module('one').component('zemAccessPermissions', {
    bindings: {
        entity: '<',
    },
    template: require('./zemAccessPermissions.component.html'),
    controller: function ($state, zemPermissions, zemUserService, zemAccessPermissionsStateService) { // eslint-disable-line max-len
        var $ctrl = this;
        $ctrl.hasPermission = zemPermissions.hasPermission;

        $ctrl.createUserData = {};
        $ctrl.stateService = zemAccessPermissionsStateService.getInstance($ctrl.entity);
        $ctrl.state = $ctrl.stateService.getState();

        $ctrl.create = create;
        $ctrl.remove = $ctrl.stateService.remove;
        $ctrl.activate = $ctrl.stateService.activate;
        $ctrl.undo = $ctrl.stateService.undo;
        $ctrl.promote = $ctrl.stateService.promote;
        $ctrl.downgrade = $ctrl.stateService.downgrade;
        $ctrl.enableApi = $ctrl.stateService.enableApi;

        $ctrl.$onInit = function () {
            $ctrl.stateService.initialize();
            $ctrl.showCollapsed = false;
        };

        function create () {
            $ctrl.stateService.create($ctrl.createUserData).then(function () {
                $ctrl.createUserData = {};
            });
        }
    },
});
