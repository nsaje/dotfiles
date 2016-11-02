angular.module('one.widgets').component('zemHeader', {
    bindings: {
        enablePublisherFilter: '=',
        showPublisherSelected: '=',
    },
    templateUrl: '/app/widgets/zem-header/zemHeader.component.html',
    controller: ['config', 'zemPermissions', function (config, zemPermissions) {
        var $ctrl = this;
        $ctrl.config = config;
        $ctrl.hasPermission = zemPermissions.hasPermission;
    }],
});
