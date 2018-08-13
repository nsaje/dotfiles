angular.module('one.widgets').component('zemBackendHacks', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<',
    },
    template: require('./zemBackendHacks.component.html'),
    controller: function($q, config, zemPermissions) {
        var $ctrl = this;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.$onInit = function() {
            $ctrl.api.register({});
        };
    },
});
