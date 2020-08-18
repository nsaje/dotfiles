angular.module('one.widgets').component('zemReportDropdown', {
    bindings: {
        api: '<',
    },
    template: require('./zemReportDropdown.component.html'),
    controller: function($uibModal, zemAuthStore) {
        var $ctrl = this;

        //
        // Public API
        //
        $ctrl.execute = execute;

        $ctrl.actions = [
            {
                name: 'Export',
                value: 'export',
                execute: openReportModal,
                hasPermission: true,
            },
        ];
        if (zemAuthStore.hasPermission('zemauth.can_see_new_report_schedule')) {
            $ctrl.actions.push({
                name: 'Schedule',
                value: 'schedule',
                execute: openScheduleModal,
                hasPermission: true,
            });
        }

        function execute(selected) {
            for (var i = 0; i < $ctrl.actions.length; i++) {
                if ($ctrl.actions[i].value === selected) {
                    $ctrl.actions[i].execute();
                    break;
                }
            }
        }

        function openReportModal() {
            $uibModal.open({
                component: 'zemReportDownload',
                windowClass: 'zem-report-download',
                backdrop: 'static',
                resolve: {
                    api: $ctrl.api,
                },
            });
        }

        function openScheduleModal() {
            $uibModal.open({
                component: 'zemReportSchedule',
                windowClass: 'zem-report-schedule',
                resolve: {
                    api: $ctrl.api,
                },
            });
        }
    },
});
