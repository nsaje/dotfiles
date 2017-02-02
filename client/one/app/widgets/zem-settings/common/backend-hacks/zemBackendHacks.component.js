angular.module('one.widgets').component('zemBackendHacks', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<',
    },
    templateUrl: '/app/widgets/zem-settings/common/backend-hacks/zemBackendHacks.component.html',
    controller: function ($q, config, zemPermissions) {
        var $ctrl = this;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.$onInit = function () {
            $ctrl.api.register({});
        };
    },
});
