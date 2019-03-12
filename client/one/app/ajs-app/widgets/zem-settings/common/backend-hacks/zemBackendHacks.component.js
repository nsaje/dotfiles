angular.module('one.widgets').component('zemBackendHacks', {
    bindings: {
        entity: '<',
        api: '<',
    },
    template: require('./zemBackendHacks.component.html'),
    controller: function($q, config, zemPermissions) {
        var $ctrl = this;
        $ctrl.showOnlyNonGlobal = true;
        $ctrl.constants = constants;

        $ctrl.filterNonGlobal = filterNonGlobal;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.$onInit = function() {
            $ctrl.api.register({});
        };
        function filterNonGlobal() {
            $ctrl.showOnlyNonGlobal = !$ctrl.showOnlyNonGlobal;
        }
    },
});
