// TODO: Replace this quick workarount to bring filters into header with refactored zem-filter-selector component
angular.module('one.widgets').component('zemHeaderFilterLegacy', {
    bindings: {
        enablePublisherFilter: '=',
        showPublisherSelected: '=',
    },
    templateUrl: '/app/widgets/zem-header/components/zem-header-filter-selector-toggle/zemHeaderFilterLegacy.component.html', // eslint-disable-line max-len
    controller: function (zemPermissions) {
        var $ctrl = this;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;
    },
});
