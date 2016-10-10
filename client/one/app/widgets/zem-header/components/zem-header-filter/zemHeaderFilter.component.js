// TODO: Replace this quick workarount to bring filters into header with refactored zem-filter component
angular.module('one.widgets').component('zemHeaderFilter', {
    bindings: {
        level: '=',
        enablePublisherFilter: '=',
        showPublisherSelected: '=',
    },
    templateUrl: '/app/widgets/zem-header/components/zem-header-filter/zemHeaderFilter.component.html',
    controller: ['zemPermissions', function (zemPermissions) {
        var $ctrl = this;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;
    }],
});
