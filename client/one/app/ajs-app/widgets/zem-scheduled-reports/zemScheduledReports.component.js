require('./zemScheduledReports.component.less');

angular.module('one.widgets').component('zemScheduledReports', {
    bindings: {
        account: '<',
    },
    template: require('./zemScheduledReports.component.html'),
    controller: function(zemScheduledReportsStateService, zemPermissions) {
        var $ctrl = this;

        $ctrl.$onInit = function() {
            var stateService = zemScheduledReportsStateService.createInstance(
                $ctrl.account
            );
            stateService.reloadReports();

            $ctrl.hasPermission = zemPermissions.hasPermission;
            $ctrl.removeReport = stateService.removeReport;
            $ctrl.state = stateService.getState();
        };
    },
});
