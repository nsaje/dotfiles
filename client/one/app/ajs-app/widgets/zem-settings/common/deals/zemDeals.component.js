angular.module('one.widgets').component('zemDeals', {
    bindings: {
        entity: '<',
        api: '<',
    },
    template: require('./zemDeals.component.html'),
    controller: function($q, config, zemPermissions) {
        var $ctrl = this;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.deals = [];
        $ctrl.showOnlyApplied = true;
        $ctrl.filterApplied = filterApplied;

        $ctrl.$onInit = function() {
            $ctrl.api.register({});
        };
        $ctrl.$onChanges = function() {
            $ctrl.deals = $ctrl.entity.deals || [];
        };
        function filterApplied() {
            $ctrl.showOnlyApplied = !$ctrl.showOnlyApplied;
        }
    },
});
