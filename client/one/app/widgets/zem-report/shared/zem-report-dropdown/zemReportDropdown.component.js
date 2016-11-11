angular.module('one.widgets').component('zemReportDropdown', {
    bindings: {
        api: '=',
    },
    templateUrl: '/app/widgets/zem-report/shared/zem-report-dropdown/zemReportDropdown.component.html',
    controller: function ($uibModal, zemPermissions) {
        var $ctrl = this;

        //
        // Public API
        //
        $ctrl.execute = execute;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.actions = [{
            name: 'Download',
            value: 'download',
            hasPermission: zemPermissions.hasPermission('zemauth.can_access_publisher_reports'),
            execute: openReportModal,
        }];

        function execute (selected) {
            for (var i = 0; i < $ctrl.actions.length; i++) {
                if ($ctrl.actions[i].value === selected) {
                    $ctrl.actions[i].execute();
                    break;
                }
            }
        }

        function openReportModal () {
            $uibModal.open({
                component: 'zemReportDownload',
                windowClass: 'model-default',
                resolve: {
                    api: $ctrl.api,
                }
            });
        }
    },
});