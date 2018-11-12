angular.module('one.widgets').component('zemAdGroupGeneralSettings', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<',
    },
    template: require('./zemAdGroupGeneralSettings.component.html'),
    controller: function(
        $scope,
        $state,
        zemPermissions,
        zemNavigationNewService,
        zemMulticurrencyService
    ) {
        var $ctrl = this;
        $ctrl.options = options;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.MESSAGES = {
            WARNING_END_DATE:
                'Your campaign has been switched to landing mode. ' +
                'Please add the budget and continue to adjust settings by your needs. ',
            INFO_CLICK_CAPPING:
                'Outbrain and Yahoo don’t support click capping and will be automatically paused in this ad group if you enable this setting.',
            WARNING_CAMPAIGN_BUDGET_OPTIMIZATION_FLIGHT_TIME:
                'Flight time settings are disabled because campaign budget ' +
                'optimization is enabled. Budget flight time is used for ' +
                'running the ad group.',
            INFO_FREQUENCY_CAPPING:
                'Outbrain and Yahoo don’t support impression frequency capping. Ads will run with no limitations on these sources.',
        };
        $ctrl.deliveryType = {
            STANDARD: 1,
            ACCELERATED: 2,
        };
        $ctrl.biddingType = constants.biddingType;

        $ctrl.startDatePicker = {isOpen: false};
        $ctrl.endDatePicker = {isOpen: false};
        $ctrl.endDatePickerOptions = {minDate: new Date()};
        $ctrl.openDatePicker = openDatePicker;
        $ctrl.goToBudgets = goToBudgets;

        $ctrl.$onInit = function() {
            initializeWatches();
            $ctrl.api.register({
                // Not needed (placeholder)
            });

            $ctrl.currencySymbol = zemMulticurrencyService.getAppropriateCurrencySymbol(
                zemNavigationNewService.getActiveAccount()
            );
        };

        function goToBudgets() {
            var campaignId = zemNavigationNewService.getActiveEntity().parent
                .id;
            $state.go('v2.analytics', {
                id: campaignId,
                level: 'campaign',
                settings: true,
                settingsScrollTo: 'zemCampaignBudgetsSettings',
            });
        }

        function initializeWatches() {
            // TODO: Refactor - remove the need for watches
            $scope.$watch('$ctrl.entity.settings.manualStop', function(
                newValue
            ) {
                if (!$ctrl.entity) return;
                if (newValue) {
                    $ctrl.entity.settings.endDate = null;
                }
            });

            $scope.$watch('$ctrl.entity.settings.endDate', function(newValue) {
                if (!$ctrl.entity) return;
                if (newValue) {
                    $ctrl.entity.settings.manualStop = false;
                } else {
                    $ctrl.entity.settings.manualStop = true;
                }
            });
        }

        function openDatePicker(type) {
            if (type === 'startDate') {
                $ctrl.startDatePicker.isOpen = true;
            } else if (type === 'endDate') {
                $ctrl.endDatePicker.isOpen = true;
            }
        }
    },
});
