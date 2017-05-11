angular.module('one.widgets').component('zemAdGroupGeneralSettings', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<',
    },
    templateUrl: '/app/widgets/zem-settings/adgroup/general/zemAdGroupGeneralSettings.component.html',
    controller: function ($scope, $state, zemPermissions, zemNavigationNewService) {
        var $ctrl = this;
        $ctrl.options = options;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.MESSAGES = {
            WARNING_END_DATE: 'Your campaign has been switched to landing mode. ' +
            'Please add the budget and continue to adjust settings by your needs. ',
            WARNING_MAX_CPM: ''
        };

        $ctrl.startDatePicker = {isOpen: false};
        $ctrl.endDatePicker = {isOpen: false};
        $ctrl.endDatePickerOptions = {minDate: new Date()};
        $ctrl.openDatePicker = openDatePicker;
        $ctrl.goToBudgets = goToBudgets;

        $ctrl.$onInit = function () {
            initializeWatches();
            $ctrl.api.register({
                // Not needed (placeholder)
            });
        };

        $ctrl.$onChanges = function () {
            if ($ctrl.entity && $ctrl.entity.warnings.maxCpm) {
                $ctrl.MESSAGES.WARNING_MAX_CPM = 'You have some active media sources ' +
                'that don\'t support max CPM restriction. To start using it, please ' +
                'disable/pause these media sources: ' +
                $ctrl.entity.warnings.maxCpm.sources.join(', ') +
                '.';
            }
        };

        function goToBudgets () {
            var campaignId = zemNavigationNewService.getActiveEntity().parent.id;
            $state.go('v2.analytics', {
                id: campaignId,
                level: 'campaign',
                settings: true,
                settingsScrollTo: 'zemCampaignBudgetsSettings'
            });
        }

        function initializeWatches () {
            // TODO: Refactor - remove the need for watches
            $scope.$watch('$ctrl.entity.settings.manualStop', function (newValue) {
                if (!$ctrl.entity) return;
                if (newValue) {
                    $ctrl.entity.settings.endDate = null;
                }
            });

            $scope.$watch('$ctrl.entity.settings.endDate', function (newValue) {
                if (!$ctrl.entity) return;
                if (newValue) {
                    $ctrl.entity.settings.manualStop = false;
                } else {
                    $ctrl.entity.settings.manualStop = true;
                }
            });
        }

        function openDatePicker (type) {
            if (type === 'startDate') {
                $ctrl.startDatePicker.isOpen = true;
            } else if (type === 'endDate') {
                $ctrl.endDatePicker.isOpen = true;
            }
        }
    },
});
