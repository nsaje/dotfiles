require('./zemScheduledReports.component.less');

angular.module('one.widgets').component('zemScheduledReports', {
    bindings: {
        account: '<',
    },
    template: require('./zemScheduledReports.component.html'),
    controller: function(zemScheduledReportsStateService, zemAuthStore) {
        var $ctrl = this;

        $ctrl.$onInit = function() {
            var stateService = zemScheduledReportsStateService.createInstance(
                $ctrl.account
            );
            stateService.reloadReports();

            $ctrl.hasPermission = zemAuthStore.hasPermission.bind(zemAuthStore);
            $ctrl.removeReport = stateService.removeReport;
            $ctrl.state = stateService.getState();
        };
    },
});
