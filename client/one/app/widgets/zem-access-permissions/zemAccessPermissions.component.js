angular.module('one').component('zemAccessPermissions', {
    bindings: {
        entity: '<',
    },
    templateUrl: '/app/widgets/zem-access-permissions/zemAccessPermissions.component.html',
    controller: function ($state, zemPermissions, zemUserService, zemAccessPermissionsDataService) { // eslint-disable-line max-len
        var $ctrl = this;
        $ctrl.hasPermission = zemPermissions.hasPermission;

        $ctrl.createUserData = {};
        $ctrl.dataService = zemAccessPermissionsDataService.getInstance($ctrl.entity);
        $ctrl.dataObject = $ctrl.dataService.getDataObject();

        $ctrl.create = $ctrl.dataService.create;
        $ctrl.remove = $ctrl.dataService.remove;
        $ctrl.activate = $ctrl.dataService.activate;
        $ctrl.undo = $ctrl.dataService.undo;
        $ctrl.promote = $ctrl.dataService.promote;
        $ctrl.downgrade = $ctrl.dataService.downgrade;

        $ctrl.$onInit = function () {
            $ctrl.dataService.initialize();
        };
    },
});
