// TODO: Replace this quick workarount to bring filters into header with refactored zem-filter component
angular.module('one.widgets').component('zemHeaderFilter', {
    bindings: {
        level: '=',
        enablePublisherFilter: '=',
        showPublisherSelected: '=',
    },
    templateUrl: '/app/widgets/zem-header/components/zem-header-filter/zemHeaderFilter.component.html',
    controller: ['zemUserService', function (zemUserService) {
        var $ctrl = this;
        $ctrl.hasPermission = zemUserService.userHasPermissions;
        $ctrl.isPermissionInternal = zemUserService.isPermissionInternal;
    }],
});
